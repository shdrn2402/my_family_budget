import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.database import get_db_connection
import psycopg
from psycopg.rows import dict_row

from bot.texts import get_text

logger = logging.getLogger(__name__)

async def inline_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all inline keyboard callback queries."""
    query = update.callback_query
    await query.answer()  # Tell Telegram we received the click
    
    user_lang = update.effective_user.language_code
    data = query.data
    
    if data == "ignore":
        return
    
    try:
        # 1. History Pagination
        if data.startswith("hist_page:"):
            from bot.handlers.history import build_history_page
            page = int(data.split(":")[1])
            text, reply_markup = await build_history_page(update.effective_user.id, user_lang, page)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')
            return

        # 1b. Account Binding
        elif data.startswith("link_acc:"):
            from bot.handlers.common import link_account_callback_handler
            await link_account_callback_handler(update, context)
            return

        # 2. Main Edit Menu (List of transactions)
        if data.startswith("edit_main:"):
            parts = data.split(":")
            tx_ids_str = parts[1]
            page = parts[2] if len(parts) > 2 else None
            
            tx_ids = [int(x) for x in tx_ids_str.split(",") if x.strip()]
            if not tx_ids:
                await query.edit_message_reply_markup(reply_markup=None)
                return
                
            async with await get_db_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    placeholders = ",".join(["%s"] * len(tx_ids))
                    await cur.execute(
                        f"SELECT id, description, amount FROM transactions WHERE id IN ({placeholders}) ORDER BY id",
                        tuple(tx_ids)
                    )
                    transactions = await cur.fetchall()
            
            keyboard = []
            for tx in transactions:
                # Pass both the context IDs and page to the next level
                keyboard.append([InlineKeyboardButton(
                    f"📝 {tx['description'].capitalize()} ({tx['amount']})", 
                    callback_data=f"edit_tx:{tx['id']}:{tx_ids_str}:{page or ''}"
                )])
            
            # Back/Close button
            if page is not None and page != "":
                # Go back to history list
                keyboard.append([InlineKeyboardButton(get_text("close_menu", user_lang), callback_data=f"hist_page:{page}")])
            else:
                # Just close (or minimize back to edit button)
                keyboard.append([InlineKeyboardButton(get_text("close_menu", user_lang), callback_data=f"minimize:{tx_ids_str}")])
                
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data.startswith("minimize:"):
            tx_ids_str = data.split(":")[1]
            keyboard = [[InlineKeyboardButton(get_text("edit_records_button", user_lang), callback_data=f"edit_main:{tx_ids_str}")]]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

        # 3. Transaction Actions (Change Category / Delete)
        elif data.startswith("edit_tx:"):
            _, tx_id, tx_ids_str, page = data.split(":")
            
            lang = user_lang or "ru"
            rename_text = "✏️ Изменить название" if lang == 'ru' else "✏️ Edit name"
            reprice_text = "💰 Изменить сумму" if lang == 'ru' else "💰 Edit amount"
            
            keyboard = [
                [InlineKeyboardButton(get_text("change_category", user_lang), callback_data=f"set_cat:{tx_id}:{tx_ids_str}:{page}")],
                [InlineKeyboardButton(rename_text, callback_data=f"rename_tx:{tx_id}:{tx_ids_str}:{page}")],
                [InlineKeyboardButton(reprice_text, callback_data=f"reprice_tx:{tx_id}:{tx_ids_str}:{page}")],
                [InlineKeyboardButton(get_text("delete", user_lang), callback_data=f"delete_tx:{tx_id}:{tx_ids_str}:{page}")],
                [InlineKeyboardButton("⬅️ " + get_text("cancel", user_lang), callback_data=f"edit_main:{tx_ids_str}:{page}")]
            ]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data.startswith("delete_tx:"):
            _, tx_id, tx_ids_str, page = data.split(":")
            async with await get_db_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("DELETE FROM transactions WHERE id = %s", (tx_id,))
                await conn.commit()
            
            await query.answer(get_text("record_deleted", user_lang))
            
            # Remove this ID from the list and go back
            remaining_ids = [x for x in tx_ids_str.split(",") if x != tx_id]
            if remaining_ids:
                new_ids_str = ",".join(remaining_ids)
                # Redirect back to the main list
                data = f"edit_main:{new_ids_str}:{page}"
                # We can't easily trigger the branch without recursion, so let's just use callback_data
                # and let the user click? No, let's just refresh the view.
                # Actually, let's just call the edit_main logic or just send them back.
                # For simplicity, let's show the success and a "Back to list" button.
                keyboard = [[InlineKeyboardButton("⬅️ " + get_text("close_menu", user_lang), callback_data=f"edit_main:{new_ids_str}:{page}")]]
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                # No more items, go back to history if possible
                if page:
                    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ " + get_text("close_menu", user_lang), callback_data=f"hist_page:{page}")]
                    ]))
                else:
                    await query.edit_message_reply_markup(reply_markup=None)
            
        elif data.startswith("rename_tx:"):
            _, tx_id, tx_ids_str, page = data.split(":")
            lang = user_lang or "ru"
            prompt_text = (
                f"Пожалуйста, напишите новое название в ответ на это сообщение.\n[ID: {tx_id}]"
                if lang == 'ru' else
                f"Please write the new name as a reply to this message.\n[ID: {tx_id}]"
            )
            from telegram import ForceReply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prompt_text,
                reply_markup=ForceReply(selective=True)
            )
            await query.answer()

        elif data.startswith("reprice_tx:"):
            _, tx_id, tx_ids_str, page = data.split(":")
            lang = user_lang or "ru"
            prompt_text = (
                f"Пожалуйста, напишите новую сумму в ответ на это сообщение.\n[ID_SUM: {tx_id}]"
                if lang == 'ru' else
                f"Please write the new amount as a reply to this message.\n[ID_SUM: {tx_id}]"
            )
            from telegram import ForceReply
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prompt_text,
                reply_markup=ForceReply(selective=True)
            )
            await query.answer()
            
        elif data.startswith("set_cat:"):
            _, tx_id, tx_ids_str, page = data.split(":")
            lang = user_lang or "ru"
            
            async with await get_db_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    await cur.execute("""
                        SELECT c.id, c.name, p.name as parent_name 
                        FROM categories c
                        JOIN categories p ON c.parent_id = p.id
                        WHERE NOT EXISTS (
                            SELECT 1 FROM categories sub
                            WHERE sub.parent_id = c.id
                        )
                        ORDER BY p.id, c.id;
                    """)
                    categories = await cur.fetchall()
            
            keyboard = []
            row = []
            current_parent = None
            
            for cat in categories:
                # get parent name
                p_name_dict = cat['parent_name']
                p_name = p_name_dict.get(lang, p_name_dict.get('ru', p_name_dict.get('en', 'Unknown')))
                
                if p_name != current_parent:
                    if row:
                        keyboard.append(row)
                        row = []
                    # Add parent separator
                    keyboard.append([InlineKeyboardButton(f"--- {p_name.upper()} ---", callback_data="ignore")])
                    current_parent = p_name
                    
                name_dict = cat['name']
                cat_name = name_dict.get(lang, name_dict.get('ru', name_dict.get('en', 'Unknown')))
                row.append(InlineKeyboardButton(cat_name, callback_data=f"save_cat:{tx_id}:{cat['id']}:{tx_ids_str}:{page}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row: keyboard.append(row)
                
            keyboard.append([InlineKeyboardButton("⬅️ " + get_text("cancel", user_lang), callback_data=f"edit_tx:{tx_id}:{tx_ids_str}:{page}")])
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data.startswith("save_cat:"):
            _, tx_id, cat_id, tx_ids_str, page = data.split(":")
            lang = user_lang or "ru"
            from bot.database import sync_category_by_alias
            
            async with await get_db_connection() as conn:
                async with conn.cursor(row_factory=dict_row) as cur:
                    cat_id_int = int(cat_id)
                    await cur.execute("SELECT amount, description, comment, user_id FROM transactions WHERE id = %s", (tx_id,))
                    row = await cur.fetchone()
                    if row:
                        current_amount = row['amount']
                        tx_user_id = row['user_id']
                        description = row['description'] or ""
                        comment = row['comment'] or ""
                        
                        # Generate composite alias string
                        alias_name = f"{description} {comment}".strip()
                        
                        # Fetch parent_id to resolve sign correctly
                        await cur.execute("SELECT parent_id FROM categories WHERE id = %s", (cat_id_int,))
                        cat_row = await cur.fetchone()
                        parent_id = cat_row['parent_id'] if cat_row else None
                        
                        from bot.services.expense import resolve_amount_sign
                        new_amount = resolve_amount_sign(current_amount, parent_id)
                        
                        await cur.execute("UPDATE transactions SET category_id = %s, amount = %s WHERE id = %s", (cat_id_int, new_amount, tx_id))
                        
                await conn.commit()
                
                # Sync aliases out of the cursor block
                if row and alias_name:
                    await sync_category_by_alias(alias_name, cat_id_int, tx_user_id, conn)
            
            confirm_text = get_text("category_saved", lang)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=confirm_text)
            
            # Go back to transaction actions
            keyboard = [[InlineKeyboardButton("⬅️ " + get_text("close_menu", user_lang), callback_data=f"edit_tx:{tx_id}:{tx_ids_str}:{page}")]]
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
            
        elif data == "close_all":
            await query.edit_message_reply_markup(reply_markup=None)
            
    except Exception as e:
        logger.error(f"Error in inline menu: {e}")
        await query.answer(get_text("unexpected_error_alert", user_lang), show_alert=True)
