import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.expense import process_expense_text
from bot.handlers.analytics import analytics_handler
from bot.handlers.common import check_access
from bot.database import get_db_connection
from bot.texts import get_text

logger = logging.getLogger(__name__)

async def expense_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Unified text message handler. Routes to analytics or saves expenses.
    """
    if not await check_access(update):
        return

    text = update.message.text
    if not text:
        return

    lang = update.effective_user.language_code
    user_id = update.effective_user.id

    # --- ANALYTICS ROUTING (Heuristic) ---
    question_keywords = [
        "сколько", "какой", "покажи", "анализ", "сводка", "отчет", "итог", "расход", "сравни", "сравнение", "график", "диаграмма",
        "how much", "show", "report", "total", "what", "analyze", "summary", "spending", "compare", "chart", "diagram"
    ]
    is_question = "?" in text or any(text.lower().startswith(word) for word in question_keywords)
    
    if is_question:
        await analytics_handler(update, context)
        return

    # --- EXPENSE PROCESSING ---
    async with await get_db_connection() as conn:
        parsed_items = await process_expense_text(text, conn)
        
        if not parsed_items:
            # If nothing was parsed and it didn't look like a question, maybe show a hint
            return

        responses = []
        async with conn.cursor() as cur:
            for item in parsed_items:
                if 'error' in item:
                    responses.append(f"❌ Error: {item['error']} for '{item.get('original', text)}'")
                    continue
                
                amount = item['amount']
                account_id = item['account_id']
                category_id = item['category_id']
                item_name = item['item_name']
                
                if not account_id:
                    responses.append(f"❌ Account not found for '{item.get('original', text)}'")
                    continue

                # Save to DB
                await cur.execute(
                    """
                    INSERT INTO transactions (user_id, account_id, category_id, amount, description, date, source_type)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, 'manual_text')
                    RETURNING id;
                    """,
                    (user_id, account_id, category_id, -abs(amount), item_name)
                )
                await conn.commit()
                responses.append(f"✅ {item_name}: {amount} ₪")

        if responses:
            await update.message.reply_text("\n".join(responses))
