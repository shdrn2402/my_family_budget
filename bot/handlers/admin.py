import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.common import check_access
from bot.services.backup import create_database_dump, export_aliases_to_yaml
from bot.database import get_db_connection
from psycopg.rows import dict_row
from bot.texts import get_text
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

async def backup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /backup command.
    Generates a database dump and an aliases.yaml export, then sends them to the user.
    """
    if not await check_access(update):
        return

    # Inform the user that the backup is starting
    message = await update.message.reply_text("⏳ Generating backup... Please wait.")
    
    try:
        # Generate files
        sql_dump_path = await create_database_dump()
        yaml_dump_path = await export_aliases_to_yaml()
        
        if not sql_dump_path or not yaml_dump_path:
            await message.edit_text("❌ Failed to generate one or more backup files. Check bot logs.")
            return
            
        # Send documents
        with open(sql_dump_path, 'rb') as sql_file:
            await update.message.reply_document(document=sql_file, filename=os.path.basename(sql_dump_path))
            
        with open(yaml_dump_path, 'rb') as yaml_file:
            await update.message.reply_document(document=yaml_file, filename=os.path.basename(yaml_dump_path))
            
        await message.edit_text("✅ Backup completed successfully!")
        
        # Cleanup is disabled so files remain in the local backups directory
            
    except Exception as e:
        logger.error(f"Error in backup handler: {e}")
        await message.edit_text(f"❌ An error occurred during backup: {e}")

async def uncategorized_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Finds and displays all transactions where category_id IS NULL.
    """
    if not await check_access(update):
        return
        
    user_id = update.effective_user.id
    lang = update.effective_user.language_code or 'ru'
    
    # Let user know we are searching
    message = await update.message.reply_text("🔍 Ищу неразмеченные транзакции..." if lang == 'ru' else "🔍 Searching for uncategorized transactions...")
    
    async with await get_db_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT id, description, amount, date FROM transactions WHERE category_id IS NULL ORDER BY date DESC"
            )
            transactions = await cur.fetchall()
            
    if not transactions:
        await message.edit_text(
            "🎉 Все транзакции размечены!" if lang == 'ru' else "🎉 All transactions are categorized!"
        )
        return
        
    await message.delete()
        
    # Group in chunks of 5 to avoid callback_data limits (64 bytes)
    chunk_size = 5
    for i in range(0, len(transactions), chunk_size):
        chunk = transactions[i:i+chunk_size]
        responses = []
        ids = []
        for tx in chunk:
            ids.append(str(tx['id']))
            amount_fmt = f"{tx['amount']:+.2f} ₪"
            date_fmt = tx['date'].strftime('%d.%m.%y')
            responses.append(f"❓ {tx['description']}: {amount_fmt} ({date_fmt})")
            
        reply_text = "\n".join(responses)
        
        keyboard = [
            [InlineKeyboardButton(get_text("edit_records_button", lang), callback_data=f"edit_main:{','.join(ids)}")]
        ]
        
        await update.message.reply_text(
            reply_text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode='HTML'
        )
