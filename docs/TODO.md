# 📌 Current Tasks (TODO)

## 1. Batch Statement Loading (Debounce)
**Goal:** When sending multiple statement files (as a batch/album), the bot should group them and send a single summary report instead of spamming messages for each file.

- [x] Implement file collector (debounce) in document handler (`bot/handlers/document.py`) with a delay of ~1.5–2 seconds.
- [x] Group files and process them in a single pass.
- [x] Output a single neat summary report:
  - Total number of rows found
  - Number of new transactions added
  - Number of duplicates skipped
- [x] Output filenames and specific errors only for statements that encountered issues during processing.
- [x] Update and expand tests to verify batch imports.

---

## 2. Cash and Bit Wallet Tracking (Reconciliation)
**Goal:** Implement correct tracking of transit operations and cash expenditures.

- [x] Add aliases for the transit account (e.g., `bit`, `paybox`) to the `account_aliases` database table.
- [x] Rewrite logic for the "Cash Withdrawal" operation (category 43): it should now be an internal transfer from the card/bank account to the `Shared Cash` account instead of a simple expense.
- [x] Add basic balance tracking for the cash wallet.
- [x] Add correlation of Bit transfers from the transit account to personal accounts.

---

## 3. LLM Refactoring: Cleaning Up Dead Code, Voice Input, Analytics

**Goal:** Remove dead and duplicate code related to LLM/analytics. Retain voice input and simple text analytics (without charts), refactoring them to match the project's architectural standards.

**Architectural Context (read before executing):**
- Charts (PNG) — remove completely. Visualization is a task for the future web application.
- In-bot analytics: only text answers to questions (NL→SQL→text). No `matplotlib`.
- Voice input: transcription via Gemini → passing text to `expense_message_handler`. Business logic duplication in `handlers/voice.py` must be eliminated.
- All user-facing strings must go through `bot/texts.py`. No hardcoded strings in Russian/English in handlers.
- All deleted tests must be recreated for the new implementation.

---

### Phase A: Dead Code Removal

- [x] **A1.** Delete `bot/services/router.py` — `classify_intent` function is not called anywhere and is dead code.
- [x] **A2.** Delete `bot/services/charts.py` — PNG charts are not needed in the bot.
- [x] **A3.** Delete `bot/temp_plots/` directory (only used for PNG charts).
- [x] **A4.** Delete `bot/handlers/analytics.py` — monolithic handler with NL→SQL→chart pipeline.
- [x] **A5.** Delete `bot/handlers/expenses.py` (empty legacy file, 0 bytes).
- [x] **A6.** Delete `bot/handlers/import_xls.py` (empty legacy file, 0 bytes).
- [x] **A7.** Delete `bot/services/excel_parser.py` (empty legacy file, 0 bytes).
- [x] **A8.** Remove tests for deleted code: `tests/test_analytics.py`, `tests/test_router.py`, `tests/test_charts.py`.
- [x] **A9.** From `bot/database.py`, delete the `execute_read_only_query` function if it is **only** used in `handlers/analytics.py`. Check with grep before deleting.
- [x] **A10.** In `bot/handlers/expense.py`, remove the `# --- ANALYTICS ROUTING (Heuristic) ---` block (lines with `question_keywords`, `is_question`, `analytics_handler`). Remove `from bot.handlers.analytics import analytics_handler` import.

---

### Phase B: Voice Input Refactoring

**Problem:** `bot/handlers/voice.py` duplicates ~80 lines of business logic from `bot/handlers/expense.py` (account type check, income check, DB INSERT). This violates the separation of concerns principle.

**Solution:** Move business logic for saving a single expense to `bot/services/expense.py`. Both handlers will call the same service.

- [x] **B1.** In `bot/services/expense.py`, create the function `save_expense_item(item: dict, user_id: int, lang: str, conn) -> dict` with the following signature:
  - Accepts a parsed `item` (with fields `item_name`, `amount`, `account_id`, `category_id`, `comment`), `user_id`, `lang`, `conn`.
  - Performs: account type check → income sign correction → INSERT → returns `{"id": int, "db_amount": float, "status": str}` or `{"error": str}`.
  - `source_type` is passed as a parameter (`'manual_text'` or `'manual_voice'`).
  - All error texts are fetched from `bot/texts.py` via `get_text()`.
  - Income triggers must be extracted into the constant `INCOME_CATEGORY_IDS = {11, 12, 13}` and `INCOME_KEYWORDS` at the top of the file, **not** inside the function body.

- [x] **B2.** Refactor `bot/handlers/expense.py`:
  - Remove duplicate block (account type check, income check, INSERT).
  - Replace it with a call to `save_expense_item()` from `services/expense.py`.
  - The handler should remain thin: get `parsed_items` → call service → format response.

- [x] **B3.** Refactor `bot/handlers/voice.py`:
  - After transcription (`transcribe_voice`) — pass text directly to `process_expense_text()`, then call `save_expense_item()`.
  - Remove the entire duplicate INSERT and checks block.
  - Replace hardcoded strings (lines 93-95, 157 in the original file) with `get_text()`.
  - The final file should contain no more than ~60 lines.

- [x] **B4.** Write test `tests/test_save_expense_item.py`:
  - Test `test_save_expense_cash_expense()`: verifies that INSERT is called with a negative amount for expenses.
  - Test `test_save_expense_income()`: verifies that the amount is positive for the income category.
  - Test `test_save_expense_card_over_limit()`: verifies that `{"error": ...}` is returned when the amount is > 150 for a card account.
  - All tests use `AsyncMock` for `conn` without a real database connection.

---

### Phase C: Analytics Refactoring (NL→SQL→Text)

**Concept:** Simple text analytics remains in the bot. Format: the user writes a question (with `?` at the beginning/end or `/ask` command) → the bot responds with text containing numbers. No charts are generated.

- [ ] **C1.** In `bot/services/llm.py`, delete the `generate_answer_from_data` function in its current form. Rewrite it: the function should accept `question: str`, `data_rows: list[dict]`, `lang: str` and return only a string response. Add an explicit return type `-> str`. Replace the hardcoded string `"Ничего не нашел..."` with `get_text("analytics_no_data", lang)`.

- [ ] **C2.** Create file `bot/handlers/query.py` — a new thin handler for analytical queries:
  - Function `query_handler(update, context)`.
  - Logic: receive text → call `llm.translate_question_to_sql()` → execute query → call `llm.generate_answer_from_data()` → send response.
  - No chart generation code.
  - No hardcoded strings — only `get_text()`.

- [ ] **C3.** In `bot/handlers/expense.py`, restore the minimalist heuristic to detect analytical queries:
  - Condition: text starts with `?` or ends with `?`.
  - If yes — call `query_handler`. Remove the fragile `question_keywords` list.

- [ ] **C4.** Register `CommandHandler("ask", query_handler)` in `bot/main.py` as an alternative way to ask questions.

- [ ] **C5.** In `bot/services/llm.py`, remove all comments and lines referring to the deleted `router.py` and `analytics.py`.

- [ ] **C6.** Write test `tests/test_query_handler.py`:
  - `test_query_handler_returns_text_answer()`: mocks `llm.translate_question_to_sql` and `llm.generate_answer_from_data`, verifies that the handler responds with text.
  - `test_query_handler_blocks_unsafe_sql()`: verifies that when `is_safe=False` the handler returns an error without executing the query.

---

### Final Check

- [ ] **F1.** Run `pytest` — all tests must pass.
- [ ] **F2.** Ensure `bot/main.py` does not import deleted modules (`analytics`, `router`, `charts`).
- [ ] **F3.** Ensure there are no direct calls to `matplotlib` and `httpx` outside `services/` in the codebase.
- [ ] **F4.** Make a commit: `refactor(llm): remove dead analytics code and deduplicate expense save logic`.

---

## 4. Import Fixes and Workflow
**Goal:** Fix the Isracard parser and simplify bulk transaction categorization.

- [x] Ignore pending transactions (without a voucher) during Isracard import to prevent data loss due to collisions.
- [x] Move alias update logic to the database level (PostgreSQL trigger on `UPDATE transactions`), eliminating duplicate Python code.
- [x] Create the `/uncategorized` command to list uncategorized transactions in Telegram with a convenient Inline keyboard.

---

## 5. Historical Cash Expense Import (Migration)
**Goal:** Develop and run a migration script to import historical cash expenses from the old bot version to populate analytics data.

- [x] Develop migration script `scripts/import_historical_cash.py` to read `bank_statements/legacy_cash_transactions_2023_2025.csv`.
- [x] Filter out transactions where `financing_source = 'Cash'`.
- [x] Map categories from the CSV file to the `seed_data.sql` structure (including parsing fuzzy categories like `Personal expenses` and `Other` using keywords in `purchase_name`).
- [x] Import transactions into the `budget.transactions` table under the account `account_id = 4` (Shared Cash).
- [x] Add duplicate prevention logic to the script for safe re-runs.
- [x] Reconcile the historical balance to zero with a single compensating transaction (top-up) on `account_id = 4` with category 43 (`Cash Withdrawal`).

---

## 6. Refactor Bit Wallet Tracking and Bit CSV Import
**Goal:** Implement full support for Bit CSV statements, establish exact reconciliation between Bit and Bank/Credit Card statements, and enhance category mapping by treating the `description + comment` composite string as the unique key for `item_aliases`.

**Context:**
- Bit acts both as a gateway for credit card payments and as a standalone wallet (transit account) holding a balance (`יתרה`).
- We can export Bit statements as CSV. The Bit CSV contains detailed transaction information (recipient/sender name) but no categorization.
- Bank/Credit Card statements only show an aggregated or generic description (e.g., `העברה ב BIT בנה"פ`).

### Phase A: Database and Categorization Refactoring
- [x] **A1.** Modify `bot/database.py` in `save_transactions_bulk` to adjust the reconciliation logic:
  - When matching Bank statement transactions, search for existing transactions where `amount` and `date` match AND `(status = 'pending' OR source_type = 'import_bit')`.
  - When updating a matched transaction, append the original description into the `comment` field (this is already implemented), but preserve the original `category_id`.
- [x] **A2.** Refactor the `item_aliases` structure and categorization logic in `bot/services/categorizer.py`:
  - When adding or updating an alias, the dictionary key should be the composite string `description + ' ' + comment` (or just `description` if `comment` is empty).
  - Modify `sync_category_by_alias` in `bot/database.py` to upsert using this composite key and update transactions matching both `description` and `comment`.

### Phase B: Bit CSV Parser Implementation
- [x] **B1.** Implement a new parser `bot/services/parsers/bit_parser.py` (or as a new function in `importer.py`):
  - Function `parse_bit_csv(file_path: str, account_id: int) -> List[Dict]`.
  - **Debit (`יתרה`):** Expense on `Transit (Bit/Paybox)` (ID: 5).
  - **Credit (`יתרה`):** Income on `Transit (Bit/Paybox)` (ID: 5).
  - **Withdrawal (`חשבון בנק`):** Internal Transfer from Transit (ID: 5) to Bank Account.
  - **Debit (`כרטיס אשראי`):** Expense on the respective Credit Card (passed via `account_id`).
  - Set `description` to the CSV `Description` column.
  - Set `comment` to the CSV `From/To` column.
  - Set `source_type` to `'import_bit'`.
  - Set `status` to `'confirmed'` for all Bit CSV transactions.
- [x] **B2.** Update `bot/handlers/imports.py` (or document handler) to detect Bit CSV files, map to the correct user's card (e.g., Andrey's or Katya's), and process the file using the new parser.

### Phase C: Testing
- [x] **C1.** Write tests for the Bit CSV parser validating the different transaction types (Credit Card, Balance Debit/Credit, Withdrawal).
- [x] **C2.** Write tests for the reconciliation logic in `bot/database.py` to ensure that a transaction with `source_type = 'import_bit'` successfully receives the `external_id` from the Bank statement without duplicating.
