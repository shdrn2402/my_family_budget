import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.importer import import_excel_file
from bot.database import save_transactions_bulk
from bot.handlers.common import check_access
from bot.texts import get_text

logger = logging.getLogger(__name__)

async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles uploaded Excel files for transaction import.
    """
    if not await check_access(update):
        return

    lang = update.effective_user.language_code
    user_id = update.effective_user.id
    
    document = update.message.document
    
    # Check file extension
    file_name = document.file_name.lower()
    if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
        # We don't reply here to avoid noise if user sends other docs, 
        # but for budget bot we can send a hint.
        await update.message.reply_text(
            "Пожалуйста, пришлите файл в формате Excel (.xls или .xlsx)" if lang == 'ru' 
            else "Please send an Excel file (.xls or .xlsx)"
        )
        return

    # Status message
    status_msg = await update.message.reply_text(
        "⏳ Обрабатываю файл..." if lang == 'ru' else "⏳ Processing file..."
    )

    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        
        # Create temp directory if not exists
        temp_dir = "temp_imports"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        file_path = os.path.join(temp_dir, f"{user_id}_{file_name}")
        await file.download_to_drive(file_path)
        
        # Parse file
        # Use caption as hint if present
        hint = update.message.caption
        transactions = import_excel_file(file_path, hint=hint)
        
        if not transactions:
            await status_msg.edit_text(
                "❌ Не удалось распознать данные в файле. Проверьте формат или имя файла (должно содержать 'isracard' или 'leumi')." if lang == 'ru'
                else "❌ Could not recognize data in the file. Check the format or filename (should contain 'isracard' or 'leumi')."
            )
            return

        # Save to DB
        inserted_count = await save_transactions_bulk(user_id, transactions)
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # Success report
        if inserted_count > 0:
            total_count = len(transactions)
            duplicates = total_count - inserted_count
            
            report = (
                f"✅ <b>Импорт завершен!</b>\n\n"
                f"📥 Всего найдено: {total_count}\n"
                f"✨ Добавлено новых: {inserted_count}\n"
                f"⏭ Пропущено дубликатов: {duplicates}"
            ) if lang == 'ru' else (
                f"✅ <b>Import complete!</b>\n\n"
                f"📥 Total found: {total_count}\n"
                f"✨ New records: {inserted_count}\n"
                f"⏭ Duplicates skipped: {duplicates}"
            )
            
            await status_msg.edit_text(report, parse_mode='HTML')
        else:
            await status_msg.edit_text(
                "👌 Новых транзакций не найдено (все уже есть в базе)." if lang == 'ru'
                else "👌 No new transactions found (all are already in the database)."
            )

    except Exception as e:
        logger.error(f"Error in document handler: {e}")
        await status_msg.edit_text(
            "❌ Произошла ошибка при обработке файла." if lang == 'ru'
            else "❌ An error occurred while processing the file."
        )
