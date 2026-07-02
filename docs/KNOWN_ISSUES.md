# Known Issues

This document tracks known bugs, limitations, and ongoing issues in the project.

## 1. Gemini AI: Refusal to translate simple nouns/brands
**Status:** Open / To Be Investigated
**Date Discovered:** June 25, 2026

**Description:**
When a user manually assigns a category to an unmapped expense (e.g., "кола" or "хлеб"), the bot runs a background task using the `gemini-flash-latest` model to auto-translate the item name and create a bilingual alias in `item_aliases`.

However, for certain simple nouns or words that the AI interprets as brand names, Gemini refuses to translate or transliterate them, completely ignoring the strict prompt instructions. For example, when asked to translate "кола", it simply returns "кола" instead of "cola" or "coca-cola". When asked to translate "хлеб", it sometimes fails to return "bread". 

**Symptoms:**
- The background translation task receives an output that is identical to the input.
- The bot logic catches `translation == text` and prevents inserting a duplicate alias.
- The user receives a Telegram message: "⚠️ Gemini решил не переводить это слово (или вернул его же)."
- No English alias is created in the database.

**Potential Workarounds/Solutions to Investigate:**
1. **Model Switch:** Switch from `gemini-flash-latest` to a more capable model (e.g., `gemini-1.5-pro` or OpenAI's `gpt-4o-mini`) specifically for the translation task.
2. **Prompt Engineering:** Use Few-Shot prompting by providing 10-15 explicit examples of "кола -> cola", "хлеб -> bread" inside the prompt to force the format.
3. **Structured Output (JSON Schema):** Force Gemini to return a JSON object with explicit fields like `{"original_alphabet": "Cyrillic", "translated_word": "cola"}` to bypass its conversational guardrails.
4. **Fallback API:** Use a traditional translation API (e.g., Google Translate API or DeepL API) instead of an LLM for simple single-word dictionary translations, as LLMs often overthink simple tasks.

## 2. Category Editing Overwrites Global Aliases
**Status:** Open / Design Decision Needed
**Date Discovered:** June 26, 2026

**Description:**
When a user manually changes the category of an individual transaction via the Telegram bot interface (in `bot/handlers/inline_menu.py`), the bot automatically executes an `INSERT ... ON CONFLICT DO UPDATE` into the `item_aliases` table. 
This means that changing the category of a single transaction permanently changes the global default category for that merchant for all future (and past, if re-imported) transactions.

**Symptoms:**
- User buys a mop for 50 ILS at a discount store (e.g., "Dan Deal") which is normally categorized as "Junk Food" (for cheap snacks).
- User changes this specific 50 ILS transaction to "Home Maintenance" via the bot.
- All future transactions from "Dan Deal" will now automatically be categorized as "Home Maintenance" instead of "Junk Food".

**Potential Workarounds/Solutions to Investigate:**
1. **User Training / Workaround:** Instruct the user to rename the transaction first (e.g., from "Dan Deal" to "Dan Deal Mop") before changing its category. This creates a new alias without touching the original.
2. **Checkbox / Inline Button Toggle:** When changing a category, ask the user: "Apply to this transaction only?" vs "Apply to all future transactions from this merchant?".
3. **Decouple Logic:** Remove the automatic alias update from the transaction edit flow completely, and rely solely on dedicated "Train Alias" workflows.

