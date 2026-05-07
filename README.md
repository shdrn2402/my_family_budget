# 💰 My Family Budget Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/YourBotLink)

**My Family Budget** is an AI-driven financial management tool built with Telegram as its primary interface. It features natural language processing for expense tracking, voice message parsing, and automated data visualization.

---

## ✨ Core Features

- 🎤 **Voice-to-Expense Parsing:** Records transactions from voice messages by automatically extracting amount, category, and description.
- 💬 **NL2SQL Analytics:** Allows querying financial history using natural language (e.g., *"How much did I spend on food last month?"*).
- 📊 **Dynamic Visualization:** Automatically generates Bar and Pie charts based on SQL query results using Matplotlib.
- 📂 **Data Ingestion:** Supports bulk transaction imports from bank statements (Excel/XLSX) with smart deduplication.
- 🔒 **Access Control:** Implements whitelist-based security using Telegram User IDs.

## 🛠 Tech Stack

- **Core:** [Python 3.10+](https://www.python.org/)
- **Bot Framework:** [python-telegram-bot](https://python-telegram-bot.org/) (PTB)
- **Database:** [PostgreSQL](https://www.postgresql.org/) + [psycopg3](https://www.psycopg.org/psycopg3/)
- **AI/LLM:** [Google Gemini 1.5 Flash](https://ai.google.dev/)
- **Data Analysis:** [Pandas](https://pandas.pydata.org/)
- **Data Viz:** [Matplotlib](https://matplotlib.org/)

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/shdrn2402/my_family_budget.git
cd my_family_budget
```

### 2. Configure Environment Variables
Copy `env.example` to `.env` and fill in your credentials:
```env
TELEGRAM_TOKEN="Your TELEGRAM Bot Token"
ALLOWED_USER_IDS="123456789, 987654321"
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=budget
DB_USER=budget_user
DB_PASSWORD=your_secure_password
GEMINI_API_KEY="your_gemini_api_key_here"
```

### 3. Run the Application
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

## 📈 Roadmap

The development progress is tracked in [ROADMAP.md](./ROADMAP.md). Future ideas and enhancements are listed in [BACKLOG.md](./BACKLOG.md).

---
*Maintained by Andrey (shdrn)*
