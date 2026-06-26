import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from bot.config import Config
from bot.texts import get_text
from bot.database import (
    check_user_exists, 
    register_user, 
    get_user_info, 
    get_user_linked_account, 
    get_unlinked_accounts, 
    link_user_to_account,
    get_db_connection
)

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
        if user_id in Config.ALLOWED_USER_IDS:
            logger.info(f"Auto-registering allowed user {user_id}")
            name: str = update.effective_user.first_name or f"User {user_id}"
            is_admin: bool = (len(Config.ALLOWED_USER_IDS) > 0 and user_id == Config.ALLOWED_USER_IDS[0])
            success: bool = await register_user(user_id, name, is_admin=is_admin)
            
            if success:
                # Attempt to auto-link to a personal account based on name
                free_accounts = await get_unlinked_accounts()
                for acc in free_accounts:
                    en_name = acc['name'].get('en', '').lower()
                    ru_name = acc['name'].get('ru', '').lower()
                    tg_name_lower = name.lower()
                    
                    if tg_name_lower == en_name or tg_name_lower == ru_name:
                        await link_user_to_account(user_id, acc['id'])
                        logger.info(f"Auto-linked user {user_id} ({name}) to account {acc['id']}")
                        break
            else:
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
    """Handle the /start command with automated or manual account linking."""
    if not await check_access(update) or not update.message or not update.effective_user:
        return
        
    user_id = update.effective_user.id
    lang = update.effective_user.language_code or 'ru'
    
    # 1. Check if user already has a linked account
    linked_account = await get_user_linked_account(user_id)
    if linked_account:
        account_name = linked_account['name'].get(lang, linked_account['name'].get('ru'))
        reply_text = (
            f"👋 С возвращением, {account_name}!\nЯ готов записывать ваши расходы."
            if lang == 'ru' else f"👋 Welcome back, {account_name}!\nI'm ready to track your expenses."
        )
        await update.message.reply_text(reply_text)
        return

    # 2. Retrieve user's family info
    user_id = update.effective_user.id
    telegram_name = update.effective_user.first_name or ""

    # Get free accounts
    free_accounts = await get_unlinked_accounts()

    # 3. Attempt auto-recognition (case-insensitive first name check)
    matched_account = None
    for acc in free_accounts:
        en_name = acc['name'].get('en', '').lower()
        ru_name = acc['name'].get('ru', '').lower()
        tg_name_lower = telegram_name.lower()
        
        if tg_name_lower == en_name or tg_name_lower == ru_name:
            matched_account = acc
            break

    if matched_account:
        success = await link_user_to_account(user_id, matched_account['id'])
        if success:
            acc_name = matched_account['name'].get(lang, matched_account['name'].get('ru'))
            reply_text = (
                f"🎉 Ура! Я автоматически распознал ваш профиль и привязал вас к счету <b>«{acc_name}»</b>.\n"
                f"Теперь ваши расходы будут записываться на этот счет."
                if lang == 'ru' else
                f"🎉 Great! I automatically recognized your profile and linked you to the account <b>«{acc_name}»</b>.\n"
                f"Your expenses will now be recorded under this account."
            )
            await update.message.reply_text(reply_text, parse_mode='HTML')
            return

    # 4. Fallback: Show interactive choices
    if not free_accounts:
        reply_text = (
            "⚠️ Все доступные персональные счета в вашей семье уже заняты.\n"
            "Пожалуйста, обратитесь к главе семьи для добавления нового счета."
            if lang == 'ru' else
            "⚠️ All available accounts in your family are already linked.\n"
            "Please ask the family head to add a new account."
        )
        await update.message.reply_text(reply_text)
        return

    keyboard = []
    for acc in free_accounts:
        acc_name = acc['name'].get(lang, acc['name'].get('ru'))
        keyboard.append([InlineKeyboardButton(f"👤 {acc_name}", callback_data=f"link_acc:{acc['id']}")] )

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    reply_text = (
        "🔍 Я не смог автоматически распознать ваш профиль.\n"
        "Пожалуйста, выберите ваш аккаунт из списка ниже:"
        if lang == 'ru' else
        "🔍 I couldn't automatically recognize your profile.\n"
        "Please select your account from the list below:"
    )
    await update.message.reply_text(reply_text, reply_markup=reply_markup)


async def link_account_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback button click for linking account."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    user_id = query.from_user.id
    lang = query.from_user.language_code or 'ru'
    
    account_id = int(query.data.split(":")[1])

    success = await link_user_to_account(user_id, account_id)
    if success:
        # Get account details
        async with await get_db_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT name FROM accounts WHERE id = %s;", (account_id,))
                acc = await cur.fetchone()
                
        acc_name = acc['name'].get(lang, acc['name'].get('ru')) if acc else ""
        
        reply_text = (
            f"✅ Успешно! Вы связали свой Telegram со счетом <b>«{acc_name}»</b>.\n"
            f"Теперь ваши расходы будут записываться на этот счет."
            if lang == 'ru' else
            f"✅ Success! You have linked your Telegram with the account <b>«{acc_name}»</b>.\n"
            f"Your expenses will now be recorded under this account."
        )
        await query.edit_message_text(reply_text, parse_mode='HTML')
    else:
        reply_text = (
            "❌ Ошибка: этот счет уже был привязан кем-то другим, либо произошел сбой базы данных.\n"
            "Пожалуйста, запустите команду /start заново."
            if lang == 'ru' else
            "❌ Error: this account has already been linked by someone else, or a database error occurred.\n"
            "Please run /start again."
        )
        await query.edit_message_text(reply_text)

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message back for testing purposes."""
    if not await check_access(update) or not update.message or not update.effective_user:
        return
        
    text: str = update.message.text or ""
    logger.info(f"Received message from {update.effective_user.id}: {text}")
    
    lang_code: str | None = update.effective_user.language_code
    reply_text: str = get_text("echo_reply", lang_code, text=text)
    
    await update.message.reply_text(reply_text)
