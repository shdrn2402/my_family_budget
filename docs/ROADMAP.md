# Development Plan: My Family Budget Bot (AI Engineer Edition)

This document describes the step-by-step implementation plan for the financial agent. The project focuses on integrating modern AI patterns (NLP, NL2SQL, Vision, MCP) to create an intelligent assistant and build a strong AI engineer portfolio.

## Phase 1: Database Foundation & Smart Data Entry (MVP)
*Goal: Set up the project architecture and implement "smart" data entry via LLM instead of legacy regular expressions.*
- [x] Database setup and user binding (`user_id`).
- [x] **Fast Data Entry (MVP):** Implementation of an ultra-fast parser based on the "item account amount" format using an alias database.
- [x] Saving structured transactions to PostgreSQL.
- [x] Integration with LLM (via API or a local model).
- [x] **NLP Data Entry (Function Calling):** Natural language free-text processing (e.g., "spent 500 on coffee yesterday in cash and 2k on fuel with credit card") — extracting entities via LLM and mapping.
- [x] Basic `/history` command to verify parsing correctness.

## Phase 2: UX Improvements & Multimodal Input (Completed ✅)
*Goal: Expand input channels and add a convenient editing interface.*
- [x] **Voice-to-Text:** Voice message processing (via Whisper/Gemini) with subsequent routing to the Phase 1 pipeline.
- [x] Inline menu after entry: `[Change Category]` and `[Delete]` buttons.
- [x] Interactive history: inline pagination and transaction management.
- [x] Statement parsing (Excel/XLSX) with automatic deduplication and bulk categorization.
- [x] **Stateless Architecture & Docker:** Refactoring into a lightweight ingestion layer and containerization.

## Phase 3: Chat with Data (Analytics via NL2SQL) [DONE]
*Goal: Replace boring statistics buttons with full conversation with data.*
- [x] **Text-to-SQL Pipeline:** Translating user questions ("How much did we spend on food this month?") into safe SQL queries.
- [x] Executing queries in the DB and generating a summary text response via LLM.
- [x] Chart generation: based on SQL query results, the bot builds charts (Pie/Bar chart) and sends them as images.
- [x] Reporting optimization: grouping by parent categories and improved chart visualization.

## Phase 4: Vision AI & Integration (MCP)
...

## Phase 5: Ergonomics and UX/UI (Polishing)
*Goal: Add final touches, make bot interaction seamless.*
- [ ] **AI-powered message routing:** Replace hardcoded keywords with a neural network classifier (Expense vs. Analytics).
- [ ] **Main menu (ReplyKeyboard):** Pack main commands (`/history`, `/stats`, etc.) into convenient buttons at the bottom of the screen.
- [ ] **User Comments & Notes (Reply style):** Add comments to transactions via replying (Reply) to the bot's message.
- [ ] Localization and interface language configuration via database.
- [ ] Improved visual format of text reports (emojis, formatting).

## Phase 6: Extended Functionality via Telegram Web App (TWA)
*Goal: Leave the bot for quick entry (on-the-go), and move complex analysis and reconciliation to a convenient Web interface.*
- [ ] Development of dashboards for statistics and budgeting visualization.
- [ ] **Statement Manager (Reconciliation UI):** Interface for convenient manual mapping of pending transactions (`pending`) with a bank statement if automatic matching failed.
- [ ] Extended management of categories, tags, and monthly budget limits.
