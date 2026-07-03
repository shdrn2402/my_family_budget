import logging
import os
import asyncio
from telegram import Update, Message
from telegram.ext import ContextTypes
from bot.services.importer import import_excel_file
from bot.database import save_transactions_bulk, get_db_connection, get_all_item_aliases
from bot.services.categorizer import auto_categorize
from bot.handlers.common import check_access
from bot.texts import get_text
from bot.services.backup import create_database_dump

logger = logging.getLogger(__name__)

# Key: user_id (int)
# Value: dict containing:
#   'documents': list[dict] - list of document info dicts
#   'status_msg': Message - the telegram message showing current status
#   'task': asyncio.Task - the active timer task that triggers batch processing
DEBOUNCE_JOBS: dict[int, dict] = {}

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles uploaded Excel files for transaction import using a debounce mechanism.
    """
    if not await check_access(update):
        return

    lang = update.effective_user.language_code or "en"
    user_id = update.effective_user.id
    
    document = update.message.document
    if not document:
        return

    # Check file extension
    file_name = document.file_name
    if not file_name:
        return
        
    file_name_lower = file_name.lower()
    if not (file_name_lower.endswith('.xlsx') or file_name_lower.endswith('.xls')):
        await update.message.reply_text(
            get_text("import_invalid_extension", lang)
        )
        return

    file_id = document.file_id
    caption = update.message.caption

    doc_info = {
        'file_id': file_id,
        'file_name': file_name,
        'caption': caption,
    }

    if user_id in DEBOUNCE_JOBS:
        # Cancel the previous timer task
        DEBOUNCE_JOBS[user_id]['task'].cancel()
        
        # Append the new document info
        DEBOUNCE_JOBS[user_id]['documents'].append(doc_info)
        
        # Update the status message to show the incremented count
        status_msg = DEBOUNCE_JOBS[user_id]['status_msg']
        count = len(DEBOUNCE_JOBS[user_id]['documents'])
        try:
            await status_msg.edit_text(
                get_text("import_status_received", lang, count=str(count))
            )
        except Exception as edit_err:
            logger.warning(f"Failed to edit status message: {edit_err}")
    else:
        # First document of the batch, create a new status message
        status_msg = await update.message.reply_text(
            get_text("import_status_received", lang, count="1")
        )
        DEBOUNCE_JOBS[user_id] = {
            'documents': [doc_info],
            'status_msg': status_msg,
            'task': None
        }

    # Start the delayed processing task
    task = asyncio.create_task(run_delayed_processing(user_id, lang, context))
    DEBOUNCE_JOBS[user_id]['task'] = task


async def run_delayed_processing(user_id: int, lang: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Waits for the debounce timer to expire, then removes the job from active list
    and initiates the batch document processing.
    """
    try:
        # Wait for the debounce delay window (1.8 seconds)
        await asyncio.sleep(1.8)
        
        # Pop the job from active jobs to allow any new incoming files to start a new batch
        job = DEBOUNCE_JOBS.pop(user_id, None)
        if not job:
            return
            
        documents = job['documents']
        status_msg = job['status_msg']
        
        # Update status message to indicate processing has started
        try:
            await status_msg.edit_text(
                get_text("import_status_processing", lang, count=str(len(documents)))
            )
        except Exception as edit_err:
            logger.warning(f"Failed to edit status message: {edit_err}")

        # Process the collected documents as a single batch
        await process_batch(user_id, documents, status_msg, lang, context)
        
    except asyncio.CancelledError:
        # Task was cancelled due to a new incoming file, which is expected behaviour
        pass
    except Exception as e:
        logger.error(f"Error in run_delayed_processing for user {user_id}: {e}", exc_info=True)


async def process_batch(
    user_id: int, 
    documents: list[dict], 
    status_msg: Message, 
    lang: str, 
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Downloads, parses, runs backup, and saves transactions for all documents in the batch.
    """
    temp_dir = "temp_imports"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    all_transactions = []
    failed_files: list[tuple[str, str]] = []

    # 1. Download and parse all documents
    for doc in documents:
        file_id = doc['file_id']
        file_name = doc['file_name']
        caption = doc['caption']
        
        file_path = os.path.join(temp_dir, f"{user_id}_{file_name}")
        
        try:
            # Download file
            file = await context.bot.get_file(file_id)
            await file.download_to_drive(file_path)
            
            # Parse file
            transactions = import_excel_file(file_path, hint=caption)
            if not transactions:
                failed_files.append((
                    file_name,
                    "No transactions recognized" if lang == 'en' else "Не удалось распознать структуру или данные"
                ))
            else:
                all_transactions.extend(transactions)
                
        except Exception as parse_err:
            logger.error(f"Error parsing file {file_name}: {parse_err}", exc_info=True)
            failed_files.append((file_name, str(parse_err)))
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to remove temp file {file_path}: {cleanup_err}")

    # If no transactions were parsed from any file, report the errors
    if not all_transactions:
        report = get_text("import_no_transactions", lang)
        if failed_files:
            report += get_text("import_report_errors", lang)
            for fname, err in failed_files:
                report += f"\n- <code>{fname}</code>: {err}"
        try:
            await status_msg.edit_text(report, parse_mode='HTML')
        except Exception as edit_err:
            logger.error(f"Failed to edit status message with errors: {edit_err}")
        return

    # 2. Perform a single database backup before importing any data
    try:
        logger.info("Creating database backup before importing transaction batch...")
        backup_path = await create_database_dump()
        if backup_path:
            logger.info(f"Database backup created successfully: {backup_path}")
        else:
            logger.warning("Failed to create database backup before importing. Proceeding with import.")
    except Exception as backup_err:
        logger.error(f"Error during pre-import backup creation: {backup_err}. Proceeding with import.")

    # 3. Save transactions to database
    inserted_count = 0
    try:
        async with await get_db_connection() as conn:
            # Load aliases to auto-categorize
            db_aliases = await get_all_item_aliases(conn)
            
            # Enrich transactions with category_id
            for tx in all_transactions:
                cat_id = auto_categorize(tx['description'], tx['amount'], db_aliases)
                if cat_id is not None:
                    tx['category_id'] = cat_id

            # Generate offsetting transactions for internal transfers (Cash & Transit)
            offsetting_transactions = []
            for tx in all_transactions:
                cat_id = tx.get('category_id')
                if cat_id == 43:  # Cash Withdrawal
                    offset_tx = tx.copy()
                    offset_tx['amount'] = -tx['amount']
                    offset_tx['account_id'] = 4  # Shared Cash
                    offset_tx['external_id'] = f"{tx.get('external_id', '')}_offset"
                    offsetting_transactions.append(offset_tx)
                elif cat_id == 15:  # Internal Transfer (Bit/Paybox)
                    offset_tx = tx.copy()
                    offset_tx['amount'] = -tx['amount']
                    offset_tx['account_id'] = 5  # Transit
                    offset_tx['external_id'] = f"{tx.get('external_id', '')}_offset"
                    offsetting_transactions.append(offset_tx)
            
            all_transactions.extend(offsetting_transactions)

            # Save to DB
            inserted_count = await save_transactions_bulk(user_id, all_transactions, conn)
    except Exception as db_err:
        logger.error(f"Database error during batch saving for user {user_id}: {db_err}", exc_info=True)
        try:
            await status_msg.edit_text(
                get_text("database_error", lang),
                parse_mode='HTML'
            )
        except Exception:
            pass
        return

    # 4. Compile success report and errors
    total_count = len(all_transactions)
    duplicates = total_count - inserted_count

    report = get_text(
        "import_report_success", 
        lang, 
        total_count=str(total_count), 
        inserted_count=str(inserted_count), 
        duplicates=str(duplicates)
    )

    if failed_files:
        report += get_text("import_report_errors", lang)
        for fname, err in failed_files:
            report += f"\n- <code>{fname}</code>: {err}"

    try:
        await status_msg.edit_text(report, parse_mode='HTML')
    except Exception as send_err:
        logger.error(f"Failed to edit final status report: {send_err}")
