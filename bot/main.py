import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.config import Config
from bot.database import init_db
from bot.handlers.common import start_handler
from bot.handlers.expense import expense_message_handler
from bot.handlers.history import history_handler
from bot.handlers.voice import voice_message_handler
from bot.handlers.document import document_handler

# Configure logging to output to console
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """Main entry point for the bot application."""
    if not Config.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set in .env!")
        return

    if not Config.ALLOWED_USER_IDS:
        logger.warning("ALLOWED_USER_IDS is empty! No one will be able to use the bot.")

    # Initialize the database
    logger.info("Checking database initialization...")
    asyncio.run(init_db())

    # Initialize the application
    application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()

    from bot.handlers.inline_menu import inline_menu_handler
    from telegram.ext import CallbackQueryHandler
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("history", history_handler))
    
    # Handler for inline keyboard clicks
    application.add_handler(CallbackQueryHandler(inline_menu_handler))
    
    # Handler for voice messages
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    
    # Handler for documents (Excel statements)
    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    
    # Handler for quick expense entry
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, expense_message_handler))

    # Global error handler
    from bot.handlers.errors import error_handler
    application.add_error_handler(error_handler)

    # Run the bot
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
