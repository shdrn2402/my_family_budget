# 💰 My Family Budget Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://t.me/YourBotLink)

**My Family Budget** is a smart AI-powered Telegram bot for family financial management. It transforms tedious expense tracking into a natural conversation, understands voice messages, and generates analytical reports based on plain text queries.

---

## ✨ Key Features

- 🎤 **Voice Command Support:** Just say: *"Spent 50 dollars on taxi"*. The bot automatically parses the amount, category, and description.
- 💬 **Chat with Data (NL2SQL):** Ask questions about your budget in natural language: *"How much did we spend on food in March?"* or *"Compare expenses by month"*.
- 📊 **Automated Visualization:** The bot automatically selects the best chart type (Pie/Bar chart) for your queries and sends a visual infographic.
- 📂 **Statement Ingestion:** Support for importing bank statements (Excel/XLSX) with automatic transaction deduplication.
- 🔒 **Secure:** Multi-user support with data protection enforced at the `user_id` level.

## 🛠 Tech Stack

- **Core:** [Python 3.10+](https://www.python.org/)
- **Bot Framework:** [Aiogram 3.x](https://docs.aiogram.dev/) (Asynchronous)
- **Database:** [PostgreSQL](https://www.postgresql.org/) + [psycopg3](https://www.psycopg.org/psycopg3/)
- **AI/LLM:** [Google Gemini API](https://ai.google.dev/) (Models: 1.5 Flash / 2.5 Flash)
- **Data Viz:** [Matplotlib](https://matplotlib.org/) (Agg backend)
- **Deployment:** Docker & Docker Compose (Ready)

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/shdrn2402/my_family_budget.git
cd my_family_budget
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
GEMINI_API_KEY=your_google_gemini_key
```

### 3. Run (via venv)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m bot.main
```

## 📈 Current Status (Roadmap)

The project is in active development. Detailed plans and completed milestones can be found in [ROADMAP.md](./ROADMAP.md).

---
*Developed with ❤️ by Andrey (shdrn)*
