# 🍍 SpongeBob Telegram Bot

An interactive Telegram bot for children, immersed in the universe of SpongeBob SquarePants. The bot uses the power of **ChatGPT (OpenAI)** to create unique fairy tales, conduct quizzes, and communicate with your favorite Bikini Bottom characters.

## 🚀 Key Features

*   **📖 Story Constructor:** Create your own stories by choosing a character, location, and theme. AI will generate a unique fairy tale just for you!
*   **🗣 Chat with Friends:** Talk to SpongeBob, Patrick, Squidward, or Number One. Each character has their own unique personality.
*   **🧠 Ask the Genius:** Get concise and clear answers to any questions from SpongeBob himself.
*   **🎮 Games and Entertainment:**
    *   **🔢 Guess the Number:** Try to guess how many bubbles SpongeBob has in mind.
    *   **✂️ Rock, Paper, Scissors:** A classic game against the bot.
    *   **❌⭕️ Tic-Tac-Toe:** A nautical version of the popular game.
*   **🐙 Marine Quiz:** Test your knowledge in a fun quiz with explanations from SpongeBob.
*   **🌐 Marine Translator:** Translate phrases into English, Ukrainian, or Russian.
*   **🧮 Counting Bubbles:** A handy calculator for little mathematicians.
*   **🎲 Random Fact:** Learn new incredible facts every day.

## 📁 Project Structure

```text
tg_bot_sponge_bob/
├── src/
│   ├── resources/
│   │   ├── images/          # Images for different bot modes
│   │   ├── messages/        # Text message templates
│   │   └── prompts/         # AI system prompts for different characters/modes
│   ├── bot.py               # Main entry point
│   ├── config.py            # Configuration and tokens
│   ├── database.py          # SQLite database management
│   ├── gpt.py               # ChatGPT service integration
│   ├── handlers.py          # Command and callback handlers logic
│   └── utils.py             # Utility functions
├── tests/                   # Pytest suite
├── README.md                # Project documentation
├── requirements.txt         # Project dependencies
└── pytest.ini               # Pytest configuration
```

## 🛠 Technologies

- **Python 3.10+**
- **python-telegram-bot:** for interaction with the Telegram API.
- **OpenAI API (GPT-3.5 Turbo):** for text generation and character logic.
- **SQLite:** for saving user profiles and their settings.
- **Pytest:** for functionality testing.

## 📦 Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/tg_bot_sponge_bob.git
   cd tg_bot_sponge_bob
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file (or edit `src/config.py`) and add your tokens:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   CHATGPT_TOKEN=your_openai_api_key
   ```

4. **Run the bot:**
   ```bash
   python src/bot.py
   ```

## 🧪 Testing

To run tests, use:
```bash
pytest
```

## 👤 Personalization

On the first launch (`/start`), the bot will suggest the child introduces themselves. It remembers:
- Child's name
- Gender (for correct character addresses)

This data is securely stored in the database and used in all modes to create the friendliest atmosphere possible.

---
*Created with love and a portion of Krabby Patties! 🍔*
