MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "access_denied": "Sorry, this bot is private.",
        "start_greeting": "Hello! I am your family budget bot 💰\nI successfully receive your messages.",
        "echo_reply": "You wrote: {text}\n(Echo test works)",
        "parse_error": "Could not recognize the expenses. Try format: 'item account amount', e.g., 'taxi card 500'",
        "item_parse_error": "❌ Error in '{original}': check format.",
        "account_not_found": "❌ Account '{alias}' not found for '{original}'",
        "expense_saved": "✅ {item} ({amount}) saved to account {account}. [{cat_status}]",
        "category_found": "Category found",
        "category_not_found": "⚠️ Category not found",
        "database_error": "An error occurred while saving to the database."
    },
    "ru": {
        "access_denied": "Извините, этот бот приватный и работает только для моей семьи.",
        "start_greeting": "Привет! Я бот для ведения семейного бюджета 💰\nЯ успешно получаю твои сообщения. Настройки БД и фильтрация готовы!",
        "echo_reply": "Вы написали: {text}\n(Эхо-проверка работает)",
        "parse_error": "Не удалось распознать покупки. Попробуйте формат: 'товар счет сумма', например 'такси кредитка 500'",
        "item_parse_error": "❌ Ошибка в '{original}': проверьте формат.",
        "account_not_found": "❌ Не найден счет для '{alias}' в '{original}'",
        "expense_saved": "✅ {item} ({amount}) сохранен на счет {account}. [{cat_status}]",
        "category_found": "Категория найдена",
        "category_not_found": "⚠️ Категория не найдена",
        "database_error": "Произошла ошибка при сохранении в базу данных."
    }
}

def get_text(key: str, lang_code: str | None = "ru", **kwargs: str) -> str:
    """
    Retrieve translated text by key.
    Fallback to English if language is not supported.
    """
    if not lang_code:
        lang_code = "en"
    lang: str = lang_code if lang_code in MESSAGES else "en"
    text: str = MESSAGES[lang].get(key, f"Missing text for {key}")
    if kwargs:
        return text.format(**kwargs)
    return text
