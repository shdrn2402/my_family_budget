import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import get_db_connection
from bot.services.expense import process_expense_text
from bot.handlers.common import check_access
from bot.texts import get_text
import psycopg

logger = logging.getLogger(__name__)

async def expense_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles regular text messages for quick expense entry.
    Example: "продукты кредитка 150.5"
    """
    if not update.message or not update.message.text:
        return

    # 0. Check access and auto-register allowed user if needed
    if not await check_access(update):
        return

    text = update.message.text
    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    
    try:
        async with await get_db_connection() as conn:
            # 1. Parse the text using the smart router
            parsed_items = await process_expense_text(text, conn)
            
            if not parsed_items:
                await update.message.reply_text(get_text("parse_error", lang))
                return
                
            responses = []
            
            # 2. Save each parsed item
            async with conn.cursor() as cur:
                for item in parsed_items:
                    if 'error' in item:
                        responses.append(get_text("item_parse_error", lang, original=item.get('original', text)))
                        continue
                        
                    # Prepare data
                    amount = item['amount']
                    account_id = item['account_id']
                    category_id = item['category_id']
                    item_name = item['item_name']
                    
                    if not account_id:
                        responses.append(get_text("account_not_found", lang, alias=item['account_alias'], original=item.get('original', text)))
                        continue
                        
                    # Insert into transactions
                    await cur.execute(
                        """
                        INSERT INTO transactions (user_id, account_id, category_id, amount, description, date, source_type)
                        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, 'manual')
                        RETURNING id;
                        """,
                        (user_id, account_id, category_id, amount, item_name)
                    )
                    
                    cat_status = get_text("category_found", lang) if category_id else get_text("category_not_found", lang)
                    responses.append(get_text("expense_saved", lang, 
                        item=item_name, 
                        amount=f"{amount:.2f}", 
                        account=item['account_alias'], 
                        cat_status=cat_status
                    ))
                
                await conn.commit()
                
            # 3. Reply to user
            await update.message.reply_text("\n".join(responses))
            
    except psycopg.Error as e:
        logger.error(f"Database error in expense handler: {e}")
        await update.message.reply_text(get_text("database_error", lang))
    except Exception as e:
        logger.error(f"Unexpected error in expense handler: {e}")
        await update.message.reply_text(get_text("database_error", lang))
