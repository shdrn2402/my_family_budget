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
