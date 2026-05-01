import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.config import Config
from bot.handlers.common import start_handler, echo_handler

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

    # Initialize the application
    application = ApplicationBuilder().token(Config.TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_handler))
    
    # Echo handler for all text messages (for testing)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

    # Run the bot
    logger.info("Starting bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
