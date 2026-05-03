import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import get_recent_transactions
from bot.handlers.common import check_access
import json

logger = logging.getLogger(__name__)

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /history command to show recent transactions."""
    if not await check_access(update) or not update.message or not update.effective_user:
        return

    user_id = update.effective_user.id
    lang = update.effective_user.language_code or "en"
    
    transactions = await get_recent_transactions(user_id, limit=10)
    
    if not transactions:
        text = "История транзакций пуста." if lang == "ru" else "Transaction history is empty."
        await update.message.reply_text(text)
        return
        
    lines = ["📊 Последние 10 транзакций:" if lang == "ru" else "📊 Last 10 transactions:"]
    
    for t in transactions:
        account_name_raw = t.get('account_name')
        
        # Handle JSONB account name formatting
        acc_name = "Unknown"
        if isinstance(account_name_raw, dict):
            acc_name = account_name_raw.get(lang, account_name_raw.get('ru', 'Unknown'))
        elif isinstance(account_name_raw, str):
            try:
                acc_dict = json.loads(account_name_raw)
                acc_name = acc_dict.get(lang, acc_dict.get('ru', 'Unknown'))
            except Exception:
                acc_name = account_name_raw
        
        # Format date
        date_val = t['date']
        date_str = date_val.strftime("%d.%m %H:%M") if hasattr(date_val, 'strftime') else str(date_val)
        
        lines.append(f"• {date_str} | {t['description']} | -{t['amount']:.2f} ({acc_name})")
        
    await update.message.reply_text("\n".join(lines))
