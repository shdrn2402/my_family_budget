import logging
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database import get_recent_transactions, get_transactions_count
from bot.handlers.common import check_access
from bot.texts import get_text

logger = logging.getLogger(__name__)

PAGE_SIZE = 5

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /history command to show recent transactions with pagination."""
    if not await check_access(update) or not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    
    text, reply_markup = await build_history_page(user_id, lang, page=0)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def build_history_page(user_id: int, lang: str | None, page: int = 0) -> tuple[str, InlineKeyboardMarkup | None]:
    """Build the text and keyboard for a specific history page."""
    offset = page * PAGE_SIZE
    
    transactions = await get_recent_transactions(user_id, limit=PAGE_SIZE, offset=offset)
    total_count = await get_transactions_count(user_id)
    
    if not transactions and page == 0:
        return get_text("history_empty", lang), None
        
    lines = [get_text("history_header", lang)]
    tx_ids = []
    
    for t in transactions:
        tx_ids.append(str(t['id']))
        acc_name = "Unknown"
        account_name_raw = t.get('account_name')
        
        if isinstance(account_name_raw, dict):
            acc_name = account_name_raw.get(lang or "en", account_name_raw.get('ru', 'Unknown'))
        
        date_val = t['date']
        date_str = date_val.strftime("%d.%m %H:%M") if hasattr(date_val, 'strftime') else str(date_val)
        
        lines.append(f"• {date_str} | {t['description']} | -{t['amount']:.2f} ({acc_name})")
        
    text = "\n".join(lines)
    
    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"hist_page:{page-1}"))
    
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE if total_count > 0 else 1
    nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    
    if (page + 1) * PAGE_SIZE < total_count:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f"hist_page:{page+1}"))
        
    keyboard = [nav_row]
    
    # Manage button for entries on THIS page
    if tx_ids:
        ids_str = ",".join(tx_ids)
        keyboard.append([InlineKeyboardButton(get_text("edit_records_button", lang), callback_data=f"edit_main:{ids_str}:{page}")])
        
    return text, InlineKeyboardMarkup(keyboard)
