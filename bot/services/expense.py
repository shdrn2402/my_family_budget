import logging
from typing import List, Dict, Any, Optional
import psycopg
from psycopg.rows import dict_row
from bot.services.llm import parse_natural_language

logger = logging.getLogger(__name__)

async def parse_expense_message(text: str, conn: psycopg.AsyncConnection) -> List[Dict[str, Any]]:
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
        
        # 4. Resolve Account ID
        account_id: Optional[int] = await resolve_account(account_alias, conn) if account_alias else 4
        if not account_id:
            account_id = 4
        
        # 5. Resolve Category ID
        category_id: Optional[int] = await resolve_category_from_alias(item_name, conn)
        
        results.append({
            'original': part,
            'item_name': item_name,
            'amount': amount,
            'account_id': account_id,
            'account_alias': account_alias,
            'category_id': category_id,
            'comment': comment
        })
        
    return results

async def resolve_account(alias: str, conn: psycopg.AsyncConnection) -> Optional[int]:
    """Find account ID from account_aliases table."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT account_id FROM account_aliases WHERE name = %s;", 
            (alias.lower(),)
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

async def process_expense_text(text: str, conn: psycopg.AsyncConnection) -> List[Dict[str, Any]]:
    """
    Smart router: tries fast regex-based parser first.
    If it encounters any formatting errors, falls back to LLM.
    """
    # 1. Try fast parser
    fast_results = await parse_expense_message(text, conn)
    
    # Check if fast parser results are complete (have amounts)
    # Re-resolving IDs with family context if necessary
    if not any('error' in item for item in fast_results):
        for item in fast_results:
            if not item.get('category_id'):
                item['category_id'] = await resolve_category_from_alias(item['item_name'], conn)
            resolved_acc = await resolve_account(item['account_alias'], conn) if item.get('account_alias') else 4
            item['account_id'] = resolved_acc if resolved_acc else 4
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
        
        resolved_acc = await resolve_account(account_alias, conn) if account_alias else 4
        account_id = resolved_acc if resolved_acc else 4
        category_id = await resolve_category_from_alias(item_name, conn)
        
        results.append({
            'original': text,
            'item_name': item_name,
            'amount': amount,
            'account_id': account_id,
            'account_alias': account_alias,
            'category_id': category_id,
            'comment': comment
        })
        
    return results
