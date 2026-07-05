import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.database import get_db_connection
from bot.services.expense import process_expense_text
from bot.services.voice import transcribe_voice
from bot.handlers.common import check_access
from bot.texts import get_text
import psycopg

logger = logging.getLogger(__name__)

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles voice messages.
    Downloads the audio, transcribes it via Gemini API, and passes it to the expense router.
    """
    if not update.message or not update.message.voice:
        return

    # 0. Check access and auto-register allowed user if needed
    if not await check_access(update):
        return

    user_id = update.effective_user.id
    lang = update.effective_user.language_code
    
    # Notify user we are processing audio
    processing_msg = await update.message.reply_text(get_text("transcribing_voice", lang))
    
    try:
        # Download audio file
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        audio_bytearray = await voice_file.download_as_bytearray()
        audio_bytes = bytes(audio_bytearray)
        
        # Transcribe
        text = await transcribe_voice(audio_bytes)
        
        if not text:
            await processing_msg.edit_text(get_text("llm_failed", lang)) # Transcription error
            return
            
        if text.startswith("__ERROR__:"):
            error_details = text.split(":", 1)[1]
            await processing_msg.edit_text(get_text("llm_failed", lang, details=error_details))
            return
            
        # Optional: Edit message to show what was heard
        heard_text = get_text("heard_voice", lang, text=text)
        await processing_msg.edit_text(heard_text, parse_mode='HTML')
        
        # Process the transcribed text as a normal expense
        async with await get_db_connection() as conn:
            from bot.database import get_user_info
            user_info = await get_user_info(user_id, conn)
            parsed_items = await process_expense_text(text, user_id, conn)
            
            if not parsed_items:
                await processing_msg.edit_text(heard_text + get_text("parse_error", lang), parse_mode='HTML')
                return
                
            responses = []
            
            total_sum = 0.0
            inserted_ids = []
            from bot.services.expense import save_expense_item
            for item in parsed_items:
                if 'error' in item:
                    if item['error'] == 'llm_failed':
                        responses.append(get_text("llm_failed", lang, details=item.get('details', '')))
                    else:
                        responses.append(get_text("item_parse_error", lang, original=item.get('original', text)))
                    continue
                    
                save_res = await save_expense_item(item, user_id, lang, conn, 'manual_voice')
                
                if "error" in save_res:
                    if save_res["error"] == "account_not_found":
                        responses.append(get_text("account_not_found", lang, alias=item.get('account_alias', ''), original=item.get('original', text)))
                    elif save_res["error"] == "card_limit_exceeded":
                        responses.append(
                            "⚠️ Траты по картам свыше 150 ₪ вносятся только через загрузку выписки." if lang == 'ru'
                            else "⚠️ Manual entry for bank cards over 150 is restricted. Please use bank statements."
                        )
                    else:
                        responses.append(get_text("item_parse_error", lang, original=item.get('original', text)))
                    continue
                    
                await conn.commit()
                
                if save_res.get("id"):
                    inserted_ids.append(str(save_res["id"]))
                
                amount = item.get('amount', 0.0)
                total_sum += amount
                
                category_id = item.get('category_id')
                item_name = item.get('item_name', '')
                
                cat_status = get_text("category_found", lang) if category_id else get_text("category_not_found", lang)
                responses.append(get_text("expense_saved", lang, 
                    item=item_name, 
                    amount=f"{amount:.2f}", 
                    account=item.get('account_alias', ''), 
                    cat_status=cat_status
                ))
                
            final_text = heard_text + "\n".join(responses)
            if total_sum > 0:
                final_text += f"\n" + get_text("total_saved", lang, amount=f"{total_sum:.2f}")
                
            if inserted_ids:
                from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                
                ids_str = ",".join(inserted_ids)
                keyboard = [
                    [InlineKeyboardButton(get_text("edit_records_button", lang), callback_data=f"edit_main:{ids_str}:")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await processing_msg.edit_text(final_text, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await processing_msg.edit_text(final_text, parse_mode='HTML')
            
    except psycopg.Error as e:
        logger.error(f"Database error in voice handler: {e}")
        await processing_msg.edit_text(get_text("database_error", lang))
    except Exception as e:
        logger.error(f"Unexpected error in voice handler: {e}")
        await processing_msg.edit_text("Произошла непредвиденная ошибка." if lang == "ru" else "An unexpected error occurred.")
