import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from bot.texts import get_text

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and notify the user about a critical failure."""
    # 1. Log the full traceback for the developer
    logger.error("Exception while handling an update:", exc_info=context.error)

    # 2. Notify the user if possible
    # update can be None or not an Update object in some cases
    if not update or not hasattr(update, "effective_user") or not update.effective_user:
        return

    user = update.effective_user
    lang = getattr(user, "language_code", "ru")
    
    # Use localized message
    error_message = get_text("unexpected_error_alert", lang)
    
    try:
        if update.effective_message:
            await update.effective_message.reply_text(f"❌ {error_message}")
    except Exception:
        # If we can't reply (e.g. user blocked the bot), just fail silently
        pass
