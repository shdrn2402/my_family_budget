import logging
from typing import List, Dict, Any, Optional
import psycopg
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
        if len(words) < 3:
            results.append({'original': part, 'error': 'not_enough_words'})
            continue
            
        # 1. Parse Amount (last word)
        try:
            amount_str: str = words[-1].replace(',', '.')
            amount: float = float(amount_str)
        except ValueError:
            results.append({'original': part, 'error': 'invalid_amount'})
            continue
            
        # 2. Parse Account Alias (second to last word)
        account_alias: str = words[-2].lower()
        
        # 3. Parse Item Name (everything before the account alias)
        item_name: str = " ".join(words[:-2]).lower()
        
        # 4. Resolve Account ID
        account_id: Optional[int] = await resolve_account(account_alias, conn)
        
        # 5. Resolve Category ID
        category_id: Optional[int] = await resolve_category_from_alias(item_name, conn)
        
        results.append({
            'original': part,
            'item_name': item_name,
            'amount': amount,
            'account_id': account_id,
            'account_alias': account_alias,
            'category_id': category_id
        })
        
    return results

async def resolve_account(alias: str, family_id: int, conn: psycopg.AsyncConnection) -> Optional[int]:
    """Find account ID from account_aliases table for a specific family."""
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT account_id FROM account_aliases WHERE name = %s AND family_id = %s;", 
            (alias.lower(), family_id)
        )
        row = await cur.fetchone()
        if row:
            return row['account_id']
    return None

async def resolve_category_from_alias(item_name: str, family_id: int, conn: psycopg.AsyncConnection) -> Optional[int]:
    """Find category ID from item_aliases table for a specific family."""
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT category_id FROM item_aliases WHERE name = %s AND family_id = %s;", 
            (item_name, family_id)
        )
        row = await cur.fetchone()
        if row:
            return row['category_id']
    return None

async def process_expense_text(text: str, family_id: int, conn: psycopg.AsyncConnection) -> List[Dict[str, Any]]:
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
                item['category_id'] = await resolve_category_from_alias(item['item_name'], family_id, conn)
            item['account_id'] = await resolve_account(item['account_alias'], family_id, conn)
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
            
        account_alias = item.get('account_alias', '')
        item_name = item.get('item_name', '')
        amount = item.get('amount', 0.0)
        
        account_id = await resolve_account(account_alias, conn) if account_alias else None
        category_id = await resolve_category_from_alias(item_name, conn)
        
        results.append({
            'original': text,
            'item_name': item_name,
            'amount': amount,
            'account_id': account_id,
            'account_alias': account_alias,
            'category_id': category_id
        })
        
    return results
