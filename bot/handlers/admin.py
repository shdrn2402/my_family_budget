import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.handlers.common import check_access
from bot.services.backup import create_database_dump, export_aliases_to_yaml

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
