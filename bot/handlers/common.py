import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config
from bot.texts import get_text
from bot.database import check_user_exists, register_user

logger = logging.getLogger(__name__)

async def check_access(update: Update) -> bool:
    """
    Check if user is allowed to use the bot.
    First checks database, then falls back to ALLOWED_USER_IDS from .env
    and auto-registers the user if they are in the allowed list.
    """
    if not update.effective_user:
        return False
        
    user_id: int = update.effective_user.id
    
    # Check if user is already in the database
    is_registered: bool = await check_user_exists(user_id)
    
    if not is_registered:
        # If not in DB, check if they are in the allowed list in .env
        if user_id in Config.ALLOWED_USER_IDS:
            logger.info(f"Auto-registering allowed user {user_id}")
            name: str = update.effective_user.first_name or f"User {user_id}"
            success: bool = await register_user(user_id, name)
            if not success:
                logger.error(f"Failed to auto-register user {user_id}")
                return False
        else:
            logger.warning(f"Unauthorized access attempt by ID {user_id}")
            
            lang_code: str | None = update.effective_user.language_code
            reply_text: str = get_text("access_denied", lang_code)
            
            if update.message:
                await update.message.reply_text(reply_text)
            return False
            
    return True

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    if not await check_access(update) or not update.message or not update.effective_user:
        return
        
    lang_code: str | None = update.effective_user.language_code
    reply_text: str = get_text("start_greeting", lang_code)
    
    await update.message.reply_text(reply_text)

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message back for testing purposes."""
    if not await check_access(update) or not update.message or not update.effective_user:
        return
        
    text: str = update.message.text or ""
    logger.info(f"Received message from {update.effective_user.id}: {text}")
    
    lang_code: str | None = update.effective_user.language_code
    reply_text: str = get_text("echo_reply", lang_code, text=text)
    
    await update.message.reply_text(reply_text)
