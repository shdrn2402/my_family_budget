import logging
import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.services import llm, charts
from bot.database import execute_read_only_query
from bot.texts import get_text

logger = logging.getLogger(__name__)

async def analytics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles natural language questions (RU/EN) about the budget.
    """
    user_id = update.effective_user.id
    question = update.message.text
    lang = update.effective_user.language_code
    
    # 1. Show "thinking" status
    status_msg = await update.message.reply_text(get_text("analytics_analyzing", lang))
    
    try:
        # 2. Translate question to SQL
        sql_data = await llm.translate_question_to_sql(question, user_id)
        
        if "error" in sql_data:
            await status_msg.edit_text(get_text("analytics_translation_error", lang, error=sql_data['error']))
            return

        if not sql_data.get("is_safe"):
            await status_msg.edit_text(get_text("analytics_unsafe_query", lang))
            return

        sql_query = sql_data["sql"]
        logger.info(f"Executing analytical SQL for {user_id}: {sql_query}")

        # 3. Execute query
        try:
            results = await execute_read_only_query(sql_query)
            db_error = None
        except Exception as e:
            results = []
            db_error = str(e)
        
        # 4. Generate human-readable answer
        answer = await llm.generate_answer_from_data(question, results, db_error)
        
        # 5. Send result
        await status_msg.edit_text(answer)

        # 6. Optional: Generate and Send Chart
        if results and len(results) > 1:
            try:
                # Prepare data for chart: first column as label, last numeric column as value
                chart_data = []
                for row in results:
                    row_values = list(row.values())
                    if len(row_values) >= 2:
                        # If it's a date/datetime, format it nicely
                        from datetime import date, datetime
                        if isinstance(row_values[0], (date, datetime)):
                            label = row_values[0].strftime("%b %Y") # e.g. Oct 2025
                        else:
                            label = str(row_values[0])

                        try:
                            # Use the last value if it's a number
                            value = float(row_values[-1])
                            chart_data.append({"label": label, "value": value})
                        except (ValueError, TypeError):
                            continue
                
                if len(chart_data) > 1:
                    # Decide chart type (heuristic)
                    # Check if the first value was a date/datetime object
                    first_val = list(results[0].values())[0]
                    from datetime import date, datetime
                    is_time_series = isinstance(first_val, (date, datetime))
                    
                    # If not a date object, fallback to keyword search in labels
                    if not is_time_series:
                        is_time_series = any(any(month in item["label"].lower() for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]) for item in chart_data)
                    
                    if is_time_series:
                        chart_path = charts.generate_bar_chart(chart_data, title="Dynamics")
                    else:
                        chart_path = charts.generate_pie_chart(chart_data, title="Structure")
                    
                    with open(chart_path, 'rb') as photo:
                        await update.message.reply_photo(photo=photo)
                    
                    # Cleanup temp file
                    os.remove(chart_path)
            except Exception as chart_err:
                logger.error(f"Chart Generation Error: {chart_err}")

    except Exception as e:
        logger.error(f"Analytics Error: {e}")
        await status_msg.edit_text(get_text("analytics_general_error", lang))
