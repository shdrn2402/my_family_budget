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

    # --- RENAME OR REPRICE TRANSACTION INTERCEPT ---
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        original_text = update.message.reply_to_message.text
        if "напишите новое название" in original_text or "write the new name" in original_text:
            import re
            match = re.search(r"\[ID:\s*(\d+)\]", original_text)
            if match:
                tx_id = int(match.group(1))
                new_name = text.strip().lower()
                
                async with await get_db_connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("UPDATE transactions SET description = %s WHERE id = %s", (new_name, tx_id))
                    await conn.commit()
                
                success_msg = f"✅ Название изменено на '{new_name}'" if lang == 'ru' else f"✅ Name changed to '{new_name}'"
                await update.message.reply_text(success_msg)
                return
        elif "напишите новую сумму" in original_text or "write the new amount" in original_text:
            import re
            match = re.search(r"\[ID_SUM:\s*(\d+)\]", original_text)
            if match:
                tx_id = int(match.group(1))
                try:
                    new_amount = float(text.strip().replace(',', '.'))
                    db_amount = -abs(new_amount)
                    
                    async with await get_db_connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("UPDATE transactions SET amount = %s WHERE id = %s", (db_amount, tx_id))
                        await conn.commit()
                    
                    success_msg = f"✅ Сумма изменена на '{new_amount}'" if lang == 'ru' else f"✅ Amount changed to '{new_amount}'"
                    await update.message.reply_text(success_msg)
                except ValueError:
                    error_msg = "❌ Пожалуйста, введите корректное число." if lang == 'ru' else "❌ Please enter a valid number."
                    await update.message.reply_text(error_msg)
                return

    # --- ANALYTICS ROUTING (Heuristic) ---
    question_keywords = [
        "сколько", "какой", "покажи", "анализ", "сводка", "отчет", "итог", "расход", "сравни", "сравнение", "график", "диаграмма",
        "дай", "структура", "структуру", "статистика", "статистику",
        "how much", "show", "report", "total", "what", "analyze", "summary", "spending", "compare", "chart", "diagram", "give", "structure", "stats"
    ]
    is_question = "?" in text or any(text.lower().startswith(word) for word in question_keywords)
    
    if is_question:
        await analytics_handler(update, context)
        return

    # --- EXPENSE PROCESSING ---
    async with await get_db_connection() as conn:
        from bot.database import get_user_info
        user_info = await get_user_info(user_id, conn)
        parsed_items = await process_expense_text(text, conn)
        
        if not parsed_items:
            # If nothing was parsed and it didn't look like a question, maybe show a hint
            return

        responses = []
        inserted_ids = []
        total_amount = 0.0

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

                # Source restriction check
                from bot.database import get_account_type
                account_type = await get_account_type(account_id, conn)
                if account_type == 'card':
                    responses.append(
                        "⚠️ Ручной ввод для банковских карт запрещен. Используйте загрузку выписок." if lang == 'ru'
                        else "⚠️ Manual entry for bank cards is restricted. Please use bank statements only."
                    )
                    continue

                comment = item.get('comment')
                
                # Save to DB
                await cur.execute(
                    """
                    INSERT INTO transactions (user_id, account_id, category_id, amount, description, comment, date, source_type)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_DATE, 'manual_text')
                    RETURNING id;
                    """,
                    (user_id, account_id, category_id, -abs(amount), item_name, comment)
                )
                res = await cur.fetchone()
                if res:
                    inserted_ids.append(str(res['id']))
                
                await conn.commit()
                
                comment_text = f" ({comment})" if comment else ""
                if category_id:
                    responses.append(f"✅ {item_name}: {amount} ₪{comment_text}")
                else:
                    warning_text = " (категория не задана)" if lang == 'ru' else " (category missing)"
                    responses.append(f"❓ {item_name}: {amount} ₪{comment_text}{warning_text}")
                
                total_amount += float(amount)

        if responses:
            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
            
            reply_text = "\n".join(responses)
            if len(inserted_ids) > 1 and total_amount > 0:
                total_label = "Итого:" if lang == 'ru' else "Total:"
                reply_text += f"\n\n<b>{total_label}</b> {total_amount:.2f} ₪"

            if inserted_ids:
                keyboard = [
                    [InlineKeyboardButton(get_text("edit_records_button", lang), callback_data=f"edit_main:{','.join(inserted_ids)}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await update.message.reply_text(reply_text, parse_mode='HTML')
