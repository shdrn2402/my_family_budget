# 📝 Backlog & Ideas (For the Future)

In this file, we will record all the cool ideas, improvements, and feature requests that pop up during development but do not block the current phase. Once the core features from `ROADMAP.md` are ready, we will return here.

## Postponed Tasks:
- [ ] **AI-Powered Universal Ingestion:** Moving away from hardcoded parsers. Using LLM to automatically determine the structure of any banking file (Excel/CSV) and map columns.
- [ ] **Multi-Family / Shared Budget Support:** Introducing `family_id` to the database. Ability to merge multiple users (husband, wife, relatives) into one "family" for a shared budget.
    - *Addition:* In history (`/history`), add filters by family members (buttons `[All]`, `[Mine]`, `[Name]`) to view both the shared expense stream and individual transactions.
- [ ] **Profile Settings Menu:** Creating a full settings menu where the user can strictly set the interface language (without relying on Telegram's `language_code`), as well as select visual themes, chart colors, and other personalizations in the future.
- [ ] **Fuzzy Search for Aliases:** If the user types an account name with a major typo, we can perform a quick local fuzzy search (e.g., via `difflib`) before sending the request to LLM. This will save time and API costs.
- [ ] **Proper Logging Setup:** Currently, errors are only written to the console (stdout). It is necessary to set up file logging with rotation (e.g., via `logging.handlers.RotatingFileHandler`) so that we can analyze errors post-factum without losing history when restarting the container or process.
- [ ] **Telegram Mini App (TMA) Dashboard:** Creating an interactive web interface directly inside Telegram. This will enable dynamic charts (Plotly/Chart.js) with filters, easy category management, and clean dashboards for the whole family.
- [ ] **Proactive AI Advisor:** A background task that analyzes expenses once a week/month, identifies anomalies ("Transport spending increased by 30%"), and gives advice on budget optimization.
- [ ] **Interactive Rule Learning:** Implementing a learning mechanism via the bot: when the user manually selects a category for a new transaction, the bot offers to "remember this rule forever" for this family (automatically creating a record in `item_aliases`).
- [ ] **Managing Accounts and Cards via Telegram (Personal Cabinet):** Ability to add, edit, and re-issue cards directly through the bot interface (without modifying the database manually).
    - *Essence:* When a user's card changes (e.g., from `4787` to `9999`), they go to "Settings/Personal Cabinet", select their account ("Andrey"), and add a new card mask to it. All transaction history for the old mask is preserved, since physical card numbers (`account_aliases`) and logical accounts (`accounts`) are completely decoupled.
- [ ] **Family Management Buttons (Admin Personal Cabinet):** Implementing an interface/menu in the bot for the Administrator (`is_admin = true`): "Add member", "Add card", "Re-issue card", etc.
