"""
Command and callback handlers for the Telegram bot.
"""
import logging
from random import choice

from telegram import Update
from telegram.ext import ContextTypes

from config import CHATGPT_TOKEN
from gpt import ChatGPTService
from utils import (send_image, send_text, load_message, show_main_menu, load_prompt, send_text_buttons)

chatgpt_service = ChatGPTService(CHATGPT_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command. Displays the welcome message and main menu.
    """
    logger.info(f"Користувач {update.effective_user.id} запустив бот")
    await send_image(update, context, "start")
    await send_text(update, context, load_message("start"))
    await show_main_menu(
        update,
        context,
        {
            'start': 'Головне меню',
            'random': 'Дізнатися випадковий факт',
            'gpt': 'Запитати мене про щось',
            'talk': 'Поговорити з мультяшними персонажами',
            'translator': 'Перекладач',
        }
    )


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /random command. Fetches and displays a random fact using GPT.
    """
    logger.info(f"Користувач {update.effective_user.id} обрав режим випадкового факту")
    await send_image(update, context, "random")
    message_to_delete = await send_text(update, context, "Шукаю випадковий факт ...")
    try:
        prompt = load_prompt("random")
        fact = await chatgpt_service.send_question(
            prompt_text=prompt,
            message_text="Розкажи про випадковий факт"
        )
        buttons = {
            'random': '💡 Хочу ще один факт',
            'start': '⬅️ Повернутись у головне меню'
        }
        await send_text_buttons(update, context, fact, buttons)
    except Exception as e:
        logger.error(f"Помилка в обробнику /random: {e}")
        await send_text(update, context, "Помилка при отриманні випадкового факту.")
    finally:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=message_to_delete.message_id
        )


async def random_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles callback queries for the random fact feature.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Користувач {update.effective_user.id} натиснув кнопку випадкового факту: {data}")
    if data == 'random':
        await random(update, context)
    elif data == 'start':
        await start(update, context)


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /gpt command. Initiates ChatGPT conversation mode.
    """
    logger.info(f"Користувач {update.effective_user.id} вибрав режим GPT")
    context.user_data.clear()
    await send_image(update, context, "gpt")
    chatgpt_service.set_prompt(load_prompt("gpt"))
    buttons = {'start': '⬅️ Повернутись у головне меню'}
    await send_text_buttons(update, context, "Запитай мене про щось ...", buttons)

    context.user_data["conversation_state"] = "gpt"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all incoming text messages based on the current conversation state.
    """
    message_text = update.message.text
    conversation_state = context.user_data.get("conversation_state")
    logger.info(f"Користувач {update.effective_user.id} надіслав повідомлення у стані {conversation_state}: {message_text[:50]}...")
    if conversation_state == "gpt":
        waiting_message = await send_text(update, context, "...")
        try:
            response = await chatgpt_service.add_message(message_text)
            buttons = {
                "start": "⬅️ Повернутись у головне меню"
            }
            await send_text_buttons(update, context, response, buttons)
        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "Виникла помилка при обробці вашого повідомлення.")
        finally:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
    elif conversation_state == "talk":
        personality = context.user_data.get("selected_personality")
        if personality:
            prompt = load_prompt(personality)
            chatgpt_service.set_prompt(prompt)
        else:
            await send_text(update, context, "Обери мультяшку, з якою хочеш поспілкуватись!")
            return
        waiting_message = await send_text(update, context, "...")
        try:
            response = await chatgpt_service.add_message(message_text)
            buttons = {"start": "⬅️ Повернутись у головне меню"}
            personality_name = personality.replace("talk_", "").replace("_", " ").title()
            await send_text_buttons(update, context, f"{personality_name}: {response}", buttons)
        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "Виникла помилка при отриманні відповіді!")
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
        finally:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
    elif conversation_state == "translator":
        target_lang = context.user_data.get("translator_lang")
        if not target_lang:
            await send_text(update, context, "Будь ласка, спочатку оберіть мову для перекладу.")
            return

        waiting_message = await send_text(update, context, "Перекладаю...")
        try:
            prompt_template = load_prompt("translator")
            prompt = prompt_template.format(target_lang=target_lang)
            translation = await chatgpt_service.send_question(prompt, message_text)

            buttons = {
                "translator_en": "English 🇺🇸",
                "translator_uk": "Українська 🇺🇦",
                "translator_ru": "Російська 🇷🇺",
                "start": "⬅️ Повернутись у головне меню"
            }
            await send_text_buttons(update, context, translation, buttons)
        except Exception as e:
            logger.error(f"Error in translator: {e}")
            await send_text(update, context, "Виникла помилка при перекладі.")
        finally:
            await context.bot.delete_message(update.effective_chat.id, waiting_message.message_id)

    if not conversation_state:
        intent_recognized = await inter_random_input(update, context, message_text)
        if not intent_recognized:
            await show_funny_response(update, context)
        return


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /talk command. Displays the list of available celebrities to chat with.
    """
    logger.info(f"Користувач {update.effective_user.id} відкрив меню вибору особистостей")
    context.user_data.clear()
    await send_image(update, context, "talk")
    personalities = {
        'talk_sponge_bob': "Sponge Bob",
        'talk_patrick_star': "Patrick Star",
        'talk_squidward_tentacles': "Squidward Tentacles",
        'talk_number_one': "Number One",
        'start': "⬅️ Повернутись у головне меню",
    }
    await send_text_buttons(update, context, "Оберіть особистість для спілкування ...", personalities)


async def gpt_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries for the GPT mode.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Користувач {update.effective_user.id} натиснув кнопку у режимі GPT: {data}")
    if data == "start":
        context.user_data.clear()
        await start(update, context)


async def talk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries for the celebrity chat mode (talk).
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Користувач {update.effective_user.id} натиснув кнопку у режимі Talk: {data}")
    if data == "start":
        context.user_data.pop("conversation_state", None)
        context.user_data.pop("selected_personality", None)
        await start(update, context)
        return
    if data == "talk":
        await talk(update, context)
        return
    if data.startswith("talk_"):
        context.user_data.clear()
        context.user_data["selected_personality"] = data
        context.user_data["conversation_state"] = "talk"
        prompt = load_prompt(data)
        chatgpt_service.set_prompt(prompt)
        personality_name = data.replace("talk_", "").replace("_", " ").title()
        await send_image(update, context, data)
        buttons = {
            'talk': "⬅️ Обрати іншу особистість",
            'start': "⬅️ Повернутись у головне меню"
        }
        await send_text_buttons(
            update,
            context,
            f"Hello, I`m {personality_name}."
            f"\nI heard you wanted to ask me something. "
            f"\nYou can ask questions in your native language.",
            buttons
        )


async def inter_random_input(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text):
    """
    Analyzes user intent to automatically switch modes based on message content.
    """
    message_text_lower = message_text.lower()
    logger.info(f"Аналіз інтенту для повідомлення: {message_text_lower[:30]}...")
    if any(keyword in message_text_lower for keyword in ['факт', 'цікав', 'random', 'випадков']):
        await send_text(
            update,
            context,
            text="Схоже, ви цікавитесь випадковими фактами! Зараз покажу вам один..."
        )
        await random(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['gpt', 'чат', 'питання', 'запита', 'дізнатися']):
        await send_text(
            update,
            context,
            text="Схоже, у вас є питання! Переходимо до режиму спілкування з ChatGPT..."
        )
        await gpt(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['розмов', 'говори', 'спілкува', 'особист', 'talk']):
        await send_text(
            update,
            context,
            text="Схоже, ви хочете поговорити з відомою особистістю! Зараз покажу вам доступні варіанти..."
        )
        await talk(update, context)
        return True
    return False


async def show_funny_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a funny AI-generated response when the user's intent is unclear.
    """
    logger.info(f"Користувач {update.effective_user.id} надіслав невідому команду, надсилаю жартівливу відповідь")
    funny_responses = [
        "Хмм... Цікаво, але я не зрозумів, що саме ви хочете. Може спробуєте одну з команд з меню?",
        "Дуже цікаве повідомлення! Але мені потрібні чіткіші інструкції. Ось доступні команди:",
        "Ой, здається, ви мене застали зненацька! Я вмію багато чого, але мені потрібна конкретна команда:",
        "Вибачте, мої алгоритми не розпізнали це як команду. Ось що я точно вмію:",
        "Це повідомлення таке ж загадкове, як єдиноріг у дикій природі! Спробуйте одну з цих команд:",
        "Я намагаюся зрозуміти ваше повідомлення... Але краще скористайтесь однією з команд:",
        "О! Випадкове повідомлення! Я теж вмію бути випадковим, але краще використовуйте команди:",
        "Гм, не спрацювало. Може спробуємо ці команди?",
        "Це повідомлення прекрасне, як веселка! Але для повноцінного спілкування спробуйте:",
        "Згідно з моїми розрахунками, це повідомлення не відповідає жодній з моїх команд. Ось вони:",
    ]
    random_response = choice(funny_responses)
    available_commands = """
    - Не знаєте, що обрати? Почніть з /start,
    - Спробуйте команду /gpt, щоб задати питання
    """
    full_message = f"{random_response}\n{available_commands}"
    await update.message.reply_text(full_message)


async def translator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /translator command. Displays language selection for translation.
    """
    logger.info(f"Користувач {update.effective_user.id} відкрив режим перекладача")
    context.user_data.clear()
    context.user_data["conversation_state"] = "translator"
    await send_image(update, context, "translator")

    buttons = {
        "translator_en": "English 🇺🇸",
        "translator_uk": "Українська 🇺🇦",
        "translator_ru": "Російська 🇷🇺",
        "start": "⬅️ Повернутись у головне меню"
    }
    await send_text_buttons(update, context, "Оберіть мову, на яку потрібно перекласти текст:", buttons)


async def translator_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries for the translator mode.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Користувач {update.effective_user.id} вибрав мову або дію у перекладачі: {data}")

    if data == "start":
        await start(update, context)
    elif data == "translator":
        await translator(update, context)
    elif data.startswith("translator_"):
        lang_code = data.replace("translator_", "")
        langs = {
            "en": "англійську",
            "uk": "українську",
            "ru": "російську",
        }
        context.user_data["translator_lang"] = langs.get(lang_code, lang_code)
        await send_text(update, context, f"Вибрано мову: {context.user_data['translator_lang']}. Надсилайте текст.")
