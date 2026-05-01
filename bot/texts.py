MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        "access_denied": "Извините, этот бот приватный и работает только для моей семьи.",
        "start_greeting": "Привет! Я бот для ведения семейного бюджета 💰\nЯ успешно получаю твои сообщения. Настройки БД и фильтрация готовы!",
        "echo_reply": "Вы написали: {text}\n(Эхо-проверка работает)"
    },
    "en": {
        "access_denied": "Sorry, this bot is private.",
        "start_greeting": "Hello! I am your family budget bot 💰\nI successfully receive your messages.",
        "echo_reply": "You wrote: {text}\n(Echo test works)"
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
