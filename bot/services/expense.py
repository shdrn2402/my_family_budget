import logging
from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from bot.services.llm import parse_natural_language
from bot.database import get_account_type
from bot.texts import get_text
import zoneinfo
from datetime import datetime, date, timedelta
from bot.config import Config

def get_local_date() -> date:
    """Returns the current date in the configured local timezone."""
    tz = zoneinfo.ZoneInfo(Config.BOT_TIMEZONE)
    return datetime.now(tz).date()


INCOME_KEYWORDS = ['доход', 'зарплата', 'подработка', 'премия', 'плюс', 'income', 'salary']

def resolve_amount_sign(amount: float, parent_id: int | None) -> float:
    """
    Determine the sign of the amount based on the category's parent.
    parent_id 1 = Income (Always positive)
    parent_id 2 = Transfer (Preserve original sign)
    all others  = Expense (Always negative)
    """
    if parent_id == 1:
        return abs(amount)
    elif parent_id == 2:
        return amount
    else:
        return -abs(amount)

logger = logging.getLogger(__name__)

async def parse_expense_message(text: str, user_id: int, conn: psycopg.AsyncConnection) -> List[Dict[str, Any]]:
    """
    Parses a string like 'кола нал 5, такси сбер 150.5'
    Returns a list of dictionaries with parsed data.
    """
    results: List[Dict[str, Any]] = []
    parts: List[str] = text.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        words: List[str] = part.split()
        
        tx_date = None
        words_lower = [w.lower() for w in words]
        
        if 'вчера' in words_lower or 'yesterday' in words_lower:
            tx_date = (get_local_date() - timedelta(days=1)).isoformat()
            target_word = 'вчера' if 'вчера' in words_lower else 'yesterday'
            words.pop(words_lower.index(target_word))
        elif 'позавчера' in words_lower:
            tx_date = (get_local_date() - timedelta(days=2)).isoformat()
            words.pop(words_lower.index('позавчера'))
        elif 'сегодня' in words_lower or 'today' in words_lower:
            tx_date = get_local_date().isoformat()
            target_word = 'сегодня' if 'сегодня' in words_lower else 'today'
            words.pop(words_lower.index(target_word))

        if len(words) < 2:
            results.append({'original': part, 'error': 'not_enough_words'})
            continue
            
        # Find amount from the end to allow optional trailing comments
        amount_idx = -1
        amount = 0.0
        for i in range(len(words)-1, 0, -1): # Need at least 1 word before amount (item_name)
            try:
                amount_str = words[i].replace(',', '.')
                amount = float(amount_str)
                amount_idx = i
                break
            except ValueError:
                continue

        if amount_idx < 1:
            results.append({'original': part, 'error': 'invalid_amount'})
            continue

        if amount_idx >= 2:
            account_alias: str = words[amount_idx - 1].lower()
            item_name: str = " ".join(words[:amount_idx - 1]).lower()
        else:
            account_alias: str = ""
            item_name: str = words[0].lower()

        comment: Optional[str] = " ".join(words[amount_idx + 1:]) if amount_idx < len(words) - 1 else None
        if comment:
            ignored_currencies = {
                'шекелей', 'шекеля', 'шекель', 'шек', 'shekels', 'shekel', 'nis', 'ils', '₪',
                'рублей', 'рубля', 'рубль', 'руб', 'rubles', 'ruble', 'rub',
                'долларов', 'доллара', 'доллар', 'dollars', 'dollar', 'usd', '$',
                'евро', 'euros', 'euro', 'eur', '€'
            }
            comment_words = comment.split()
            filtered_comment_words = []
            for w in comment_words:
                clean_w = w.lower().strip('.,!?;:')
                if clean_w not in ignored_currencies:
                    filtered_comment_words.append(w)
            comment = " ".join(filtered_comment_words) if filtered_comment_words else None
        
        # 4. Resolve Account ID
        account_id: Optional[int] = await resolve_account(account_alias, user_id, conn) if account_alias else None
        
        # If an account was supposedly provided but we couldn't resolve it, this is likely natural language.
        # We append an error to trigger LLM fallback.
        if account_alias and not account_id:
            results.append({'original': part, 'error': 'account_not_found_fallback'})
            continue
        
        # 5. Resolve Category ID
        category_id: Optional[int] = await resolve_category_from_alias(item_name, conn)
        
        results.append({
            'original': part,
            'item_name': item_name,
            'amount': amount,
            'account_id': account_id,
            'account_alias': account_alias,
            'category_id': category_id,
            'comment': comment,
            'date': tx_date
        })
        
    return results

async def resolve_account(alias: str, user_id: int, conn: psycopg.AsyncConnection) -> Optional[int]:
    """Find account ID from account_aliases table or dynamically via owner_id."""
    alias = alias.lower().strip()
    if alias in ['карта', 'card']:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT id FROM accounts WHERE type = 'card' AND owner_id = %s LIMIT 1;",
                (user_id,)
            )
            row = await cur.fetchone()
            if row:
                return row['id']
            return None

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT account_id FROM account_aliases WHERE name = %s;", 
            (alias,)
        )
        row = await cur.fetchone()
        if row:
            return row['account_id']
    return None

async def resolve_category_from_alias(item_name: str, conn: psycopg.AsyncConnection) -> Optional[int]:
    """Find category ID from item_aliases table."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT category_id FROM item_aliases WHERE name = %s;", 
            (item_name.lower().strip(),)
        )
        row = await cur.fetchone()
        if row:
            return row['category_id']
    return None

async def process_expense_text(text: str, user_id: int, conn: psycopg.AsyncConnection) -> List[Dict[str, Any]]:
    """
    Smart router: tries fast regex-based parser first.
    If it encounters any formatting errors, falls back to LLM.
    """
    # 1. Try fast parser
    fast_results = await parse_expense_message(text, user_id, conn)
    
    # Check if fast parser results are complete (have amounts)
    # Re-resolving IDs with family context if necessary
    if not any('error' in item for item in fast_results):
        for item in fast_results:
            if not item.get('category_id'):
                item['category_id'] = await resolve_category_from_alias(item['item_name'], conn)
            resolved_acc = await resolve_account(item['account_alias'], user_id, conn) if item.get('account_alias') else None
            item['account_id'] = resolved_acc
        return fast_results

    # 2. Fallback to LLM
    logger.info("Falling back to LLM for: %s", text)
    llm_items = await parse_natural_language(text)
    
    # Resolve aliases for LLM results
    results = []
    for item in llm_items:
        if 'error' in item:
            results.append(item)
            continue
            
        account_alias = item.get('account_alias', '').strip().lower()
        item_name = item.get('item_name', '').strip().lower()
        amount = item.get('amount', 0.0)
        comment = item.get('comment', None)
        
        resolved_acc = await resolve_account(account_alias, user_id, conn) if account_alias else None
        account_id = resolved_acc
        category_id = await resolve_category_from_alias(item_name, conn)
        tx_date = item.get('date')
        
        results.append({
            'original': text,
            'item_name': item_name,
            'amount': amount,
            'account_id': account_id,
            'account_alias': account_alias,
            'category_id': category_id,
            'comment': comment,
            'date': tx_date
        })
        
    return results

async def save_expense_item(item: dict, user_id: int, lang: str, conn: psycopg.AsyncConnection, source_type: str) -> dict:
    """
    Saves a single parsed expense item to the database.
    Checks account type limits, identifies income vs expense, and inserts into DB.
    Returns {"id": int, "db_amount": float, "status": str} on success,
    or {"error": str} on failure.
    """
    amount = item.get('amount', 0.0)
    account_id = item.get('account_id')
    category_id = item.get('category_id')
    item_name = item.get('item_name', '')
    comment = item.get('comment')
    
    if not account_id:
        return {"error": "account_not_found"}
        
    account_type = await get_account_type(account_id, conn)
    status = 'confirmed' if account_type == 'cash' else 'pending'
    
    if account_type == 'card':
        if abs(amount) > 150:
            return {"error": "card_limit_exceeded"}
        
    parent_id = None
    if category_id:
        async with conn.cursor() as cur:
            await cur.execute("SELECT parent_id FROM categories WHERE id = %s", (category_id,))
            cat_row = await cur.fetchone()
            if cat_row:
                # `cat_row` might be a tuple or dict depending on row_factory, let's handle both safely
                parent_id = cat_row[0] if isinstance(cat_row, tuple) else cat_row.get('parent_id')

    # If it matched no category but has income keywords, fallback to Other Income (13)
    if not category_id and any(word in item_name.split() for word in INCOME_KEYWORDS):
        category_id = 13
        parent_id = 1

    db_amount = resolve_amount_sign(amount, parent_id)
    
    tx_date = item.get('date') or get_local_date().isoformat()
    
    query = """
        INSERT INTO transactions (user_id, account_id, category_id, amount, description, comment, date, source_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s::date, %s, %s)
        RETURNING id;
    """
    
    params = [user_id, account_id, category_id, db_amount, item_name, comment, tx_date, source_type, status]
    
    async with conn.cursor() as cur:
        await cur.execute(query, tuple(params))
        row = await cur.fetchone()
        
    return {
        "id": row['id'] if row else None,
        "db_amount": db_amount,
        "status": status
    }
