"""
Main entry point for the Telegram bot.
Initializes the bot and registers all command and callback handlers.
"""
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN
from database import init_db
from handlers import (
    start, random, random_button, gpt, message_handler, talk, talk_button,
    translator, translator_button, gpt_button, calc, calc_button, registration_button,
    quiz, quiz_button, game, game_button, tictactoe, tictactoe_button,
    story, story_button, numbers, numbers_button
)


# Initialize database
init_db()

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("random", random))
app.add_handler(CommandHandler("gpt", gpt))
app.add_handler(CommandHandler("talk", talk))
app.add_handler(CommandHandler("translator", translator))
app.add_handler(CommandHandler("calc", calc))
app.add_handler(CommandHandler("quiz", quiz))
app.add_handler(CommandHandler("game", game))
app.add_handler(CommandHandler("tictactoe", tictactoe))
app.add_handler(CommandHandler("story", story))
app.add_handler(CommandHandler("numbers", numbers))
app.add_handler(CallbackQueryHandler(story_button, pattern='^story.*$'))

app.add_handler(CallbackQueryHandler(gpt_button, pattern='^start$'))
app.add_handler(CallbackQueryHandler(random_button, pattern='^(random|start)$'))
app.add_handler(
    CallbackQueryHandler(talk_button, pattern='^talk_.*|^talk$|^start$')
)
app.add_handler(
    CallbackQueryHandler(translator_button, pattern='^translator.*|^start$')
)
app.add_handler(CallbackQueryHandler(calc_button, pattern='^calc_.*$'))
app.add_handler(CallbackQueryHandler(quiz_button, pattern='^quiz_.*$'))
app.add_handler(CallbackQueryHandler(game_button, pattern='^game_.*$'))
app.add_handler(CallbackQueryHandler(numbers_button, pattern='^numbers_.*$'))
app.add_handler(CallbackQueryHandler(tictactoe_button, pattern='^ttt_.*$'))
app.add_handler(CallbackQueryHandler(registration_button, pattern='^registration_.*$'))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
