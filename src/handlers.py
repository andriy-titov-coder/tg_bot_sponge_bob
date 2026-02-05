"""
Command and callback handlers for the Telegram bot.
"""
import logging
from random import choice

from telegram import Update
from telegram.ext import ContextTypes

from config import CHATGPT_TOKEN
from gpt import ChatGPTService
from utils import (send_image, send_text, load_message, show_main_menu, load_prompt, send_text_buttons, send_main_menu_reply)
from database import get_user, save_user

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
    Handles the /start command. Checks if user is registered, otherwise starts registration.
    """
    user_id = update.effective_user.id
    user_profile = get_user(user_id)

    if not user_profile:
        logger.info(f"Новий користувач {user_id}, починаємо реєстрацію")
        context.user_data.clear()
        context.user_data["conversation_state"] = "registration_name"
        await send_image(update, context, "start")
        await send_text(update, context, "ПРИВІТ! Я Губка Боб! 🍍 Я такий радий тебе бачити! "
                                        "\nАле стривай... я ще не знаю твого імені! 😱"
                                        "\nЯк тебе звати, друже?")
        return

    # Зберігаємо профіль у context для швидкого доступу
    context.user_data["user_profile"] = user_profile
    
    logger.info(f"Користувач {user_id} ({user_profile['name']}) запустив бот")
    await send_image(update, context, "start")
    
    menu_buttons = {
        'start': '🏠 Головне меню',
        'random': '🎲 Випадкова цікавинка',
        'gpt': '🧠 Запитати в Розумника',
        'talk': '🗣 Побалакати з друзями',
        'translator': '🌐 Морський перекладач',
        'calc': '🧮 Рахуємо бульбашки',
    }
    
    name = user_profile["name"]
    welcome_msg = load_message("start").replace("{name}", name)
    
    await send_main_menu_reply(
        update, 
        context, 
        welcome_msg, 
        list(menu_buttons.values())
    )
    
    await show_main_menu(update, context, menu_buttons)


async def registration_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles gender selection during registration.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("registration_gender_"):
        gender = data.replace("registration_gender_", "")
        name = context.user_data.get("reg_name")
        
        save_user(user_id, name, gender)
        user_profile = {"name": name, "gender": gender}
        context.user_data["user_profile"] = user_profile
        context.user_data.pop("conversation_state", None)
        
        gender_text = "друже" if gender == "boy" else "подруго"
        await send_text(update, context, f"УРААА! 🎉 Тепер ми офіційно друзі, {name}! "
                                        f"\nЯ запам'ятав, що ти — найкращий у світі {gender_text}! "
                                        f"\nГотовий до пригод у Бікіні Боттом? Тисни /start!")


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /random command. Fetches and displays a random fact using GPT.
    """
    logger.info(f"Користувач {update.effective_user.id} обрав режим випадкового факту")
    await send_image(update, context, "random")
    
    user_profile = context.user_data.get("user_profile")
    name = user_profile["name"] if user_profile else "друже"
    message_to_delete = await send_text(update, context, f"Зараз-зараз, {name}, виловлюю найкрутіший факт із океану знань... 🫧")
    try:
        prompt = load_prompt("random")
        fact = await chatgpt_service.send_question(
            prompt_text=prompt,
            message_text="Розкажи про випадковий факт"
        )
        buttons = {
            'random': '💡 Хочу ще одну цікавинку!',
            'start': '⬅️ Назад до крабсбургерів'
        }
        await send_text_buttons(update, context, fact, buttons)
    except Exception as e:
        logger.error(f"Помилка в обробнику /random: {e}")
        await send_text(update, context, "Ой-йой, медуза вжалила систему! Не можу знайти факт... 🐙")
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
    user_profile = context.user_data.get("user_profile")
    context.user_data.clear()
    context.user_data["user_profile"] = user_profile
    
    name = user_profile["name"] if user_profile else ""
    gender_text = "друже" if user_profile and user_profile.get("gender") == "boy" else "подруго"
    
    await send_image(update, context, "gpt")
    chatgpt_service.set_prompt(load_prompt("gpt") + f"\nКористувач: {name}, Стать: {user_profile['gender'] if user_profile else 'невідомо'}")
    buttons = {'start': '⬅️ Додому в Ананас'}
    await send_text_buttons(update, context, f"Я готовий! Я готовий! Запитай мене про що завгодно, {name}! 🍍✨", buttons)

    context.user_data["conversation_state"] = "gpt"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles all incoming text messages based on the current conversation state.
    """
    message_text = update.message.text
    conversation_state = context.user_data.get("conversation_state")
    logger.info(f"Користувач {update.effective_user.id} надіслав повідомлення у стані {conversation_state}: {message_text[:50]}...")

    if conversation_state == "registration_name":
        context.user_data["reg_name"] = message_text
        context.user_data["conversation_state"] = "registration_gender"
        buttons = {
            "registration_gender_boy": "Я Хлопчик! 👦",
            "registration_gender_girl": "Я Дівчинка! 👧"
        }
        await send_text_buttons(update, context, f"Дуже приємно, {message_text}! 🤝 А тепер скажи мені по секрету... ти хлопчик чи дівчинка?", buttons)
        return

    if conversation_state == "calc":
        step = context.user_data.get("calc_step", "first")

        user_profile = context.user_data.get("user_profile")
        name = user_profile["name"] if user_profile else "друже"
        gender_suffix = "" if user_profile and user_profile.get("gender") == "boy" else "а"
        
        if step == "first":
            a = _parse_number(message_text)
            if a is None:
                await send_text(update, context, f"Гаррі, це не число! 🐌 Спробуй ще раз, {name}!")
                return

            context.user_data["calc_a"] = a
            context.user_data["calc_step"] = "op"

            buttons = {
                "calc_op_+": "+",
                "calc_op_-": "-",
                "calc_op_*": "*",
                "calc_op_/": "/",
                "start": "⬅️ Назад до медуз",
            }
            await send_text_buttons(update, context, "Ух ти! І що ми з ним зробимо? 😏 Обери магічну дію:", buttons)
            return

        if step == "second":
            b = _parse_number(message_text)
            if b is None:
                gender_ref = "як Патрік" if user_profile and user_profile.get("gender") == "boy" else "як зірочка"
                await send_text(update, context, f"Ой-ой! Це точно не число! Спробуй ще раз, {gender_ref}! ⭐️")
                return

            a = float(context.user_data["calc_a"])
            op = context.user_data.get("calc_op")

            if op == "/" and _is_close(b, 0.0):
                context.user_data["calc_step"] = "second"
                await send_text(update, context, "Тартарський соус! 🍔 На нуль ділити не можна, навіть у Бікіні Боттом! Введи інше число.")
                return

            if op == "+":
                correct = a + b
            elif op == "-":
                correct = a - b
            elif op == "*":
                correct = a * b
            elif op == "/":
                correct = a / b
            else:
                await send_text(update, context, "Щось я заплутався в водоростях... 🌿 Натисни кнопку з дією!")
                context.user_data["calc_step"] = "op"
                return

            context.user_data["calc_b"] = b
            context.user_data["calc_correct"] = correct
            context.user_data["calc_attempts"] = 0
            context.user_data["calc_step"] = "answer"

            expr = f"{_format_number(a)} {op} {_format_number(b)}"
            await send_text(
                update,
                context,
                _md_escape(f"Скільки буде {expr}? Спроба 1 з 3. Чекаю твою відповідь! ⚓️")
            )
            return

        if step == "answer":
            user_answer = _parse_number(message_text)
            if user_answer is None:
                await send_text(update, context, "Потрібне число, друже! Порахуй на пальцях... або на щупальцях! 🐙")
                return

            correct = float(context.user_data["calc_correct"])
            attempts = int(context.user_data.get("calc_attempts", 0))

            if _answers_match(user_answer, correct, message_text):
                buttons = {
                    "calc_again": "🔁 Ще приклад!",
                    "start": "⬅️ Назад до Лагуни",
                }
                context.user_data["calc_step"] = "first"
                congrats = "Ти просто геній, як Сенді!" if user_profile and user_profile.get("gender") == "boy" else "Ти просто геніальна, як Сенді!"
                await send_text_buttons(update, context, f"ПРАВИЛЬНО! {congrats} 🐿✨", buttons)
                return

            attempts += 1
            context.user_data["calc_attempts"] = attempts

            a = float(context.user_data["calc_a"])
            b = float(context.user_data["calc_b"])
            op = context.user_data["calc_op"]

            if attempts < 3:
                expr = f"{_format_number(a)} {op} {_format_number(b)}"
                await send_text(
                    update,
                    context,
                    _md_escape(f"Не вийшло... але не здавайся! 🌈 Спроба {attempts + 1} з 3. Скільки буде {expr}?")
                )
                return

            buttons = {
                "calc_again": "🔁 Ще приклад!",
                "start": "⬅️ Назад до меню",
            }
            context.user_data["calc_step"] = "first"
            await send_text_buttons(update, context, f"Ой, три спроби пролетіли, як медузи! 🪼 Правильна відповідь: {_format_number(correct)}.",
                                    buttons)
            return

        # Якщо раптом step зламався
        context.user_data["calc_step"] = "first"
        await send_text(update, context, "Ой-ой, щось пішло не так під водою! Давай спочатку. Введи перше число! 🍍")
        return

    if conversation_state == "gpt":
        waiting_message = await send_text(update, context, "...")
        try:
            response = await chatgpt_service.add_message(message_text)
            buttons = {
                "start": "⬅️ Назад на берег"
            }
            await send_text_buttons(update, context, response, buttons)
        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "Тартарський соус! Щось зламалось у моїх мізках... 🧠💦 Спробуй ще раз пізніше!")
        finally:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
    elif conversation_state == "talk":
        user_profile = context.user_data.get("user_profile")
        name = user_profile["name"] if user_profile else "друже"
        gender = user_profile["gender"] if user_profile else "невідомо"
        
        personality = context.user_data.get("selected_personality")
        if personality:
            prompt = load_prompt(personality)
            chatgpt_service.set_prompt(prompt + f"\nКористувач: {name}, Стать: {gender}")
        else:
            await send_text(update, context, "Гей! Спочатку обери, з ким хочеш потеревенити! 🗣🐙")
            return
        waiting_message = await send_text(update, context, "...")
        try:
            response = await chatgpt_service.add_message(message_text)
            buttons = {"start": "⬅️ Додому в Ананас"}
            personality_name = personality.replace("talk_", "").replace("_", " ").title()
            await send_text_buttons(update, context, f"{personality_name}: {response}", buttons)
        except Exception as e:
            logger.error(f"Помилка при отриманні відповіді від ChatGPT: {e}")
            await send_text(update, context, "Ой! Здається, твій друг кудись зник під воду... 🌊 Спробуй ще раз!")
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
        finally:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
    elif conversation_state == "translator":
        user_profile = context.user_data.get("user_profile")
        name = user_profile["name"] if user_profile else "друже"
        
        target_lang = context.user_data.get("translator_lang")
        if not target_lang:
            await send_text(update, context, f"Крабсбургер мені в рот, {name}! Ти ж не вибрав мову! 🍔 Обери швидше!")
            return

        waiting_message = await send_text(update, context, "Перекладаю на морську мову... 🫧")
        try:
            prompt_template = load_prompt("translator")
            prompt = prompt_template.format(target_lang=target_lang)
            translation = await chatgpt_service.send_question(prompt, message_text)

            buttons = {
                "translator_en": "English 🇺🇸",
                "translator_uk": "Українська 🇺🇦",
                "translator_ru": "Російська 🇷🇺",
                "start": "⬅️ Назад до меню"
            }
            await send_text_buttons(update, context, translation, buttons)
        except Exception as e:
            logger.error(f"Error in translator: {e}")
            await send_text(update, context, "Щось переклад застряг у водоростях... 🌿 Спробуй іншу фразу!")
        finally:
            await context.bot.delete_message(update.effective_chat.id, waiting_message.message_id)

    if not conversation_state:
        # Обробка фізичних кнопок головного меню
        if message_text == '🎲 Випадкова цікавинка':
            await random(update, context)
            return
        if message_text == '🧠 Запитати в Розумника':
            await gpt(update, context)
            return
        if message_text == '🗣 Побалакати з друзями':
            await talk(update, context)
            return
        if message_text == '🌐 Морський перекладач':
            await translator(update, context)
            return
        if message_text == '🧮 Рахуємо бульбашки':
            await calc(update, context)
            return
        if message_text == '🏠 Головне меню':
            await start(update, context)
            return

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
        'start': "⬅️ Назад до Ананаса",
    }
    await send_text_buttons(update, context, "Ого! З ким хочеш потеревенити сьогодні? Обирай свого героя! 🗣✨", personalities)


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
        user_profile = context.user_data.get("user_profile")
        name = user_profile["name"] if user_profile else "friend"
        gender = user_profile["gender"] if user_profile else "unknown"
        
        context.user_data.clear()
        context.user_data["user_profile"] = user_profile
        context.user_data["selected_personality"] = data
        context.user_data["conversation_state"] = "talk"
        prompt = load_prompt(data)
        chatgpt_service.set_prompt(prompt + f"\nКористувач: {name}, Стать: {gender}")
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
            text="Ух ти! Схоже, ти шукаєш щось цікавеньке! Зараз виловлю для тебе факт... 🎲🫧"
        )
        await random(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['gpt', 'чат', 'питання', 'запита', 'дізнатися']):
        await send_text(
            update,
            context,
            text="Ого! Схоже, у тебе є питання! Давай запитаємо у Розумника! 🧠✨"
        )
        await gpt(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ['розмов', 'говори', 'спілкува', 'особист', 'talk']):
        await send_text(
            update,
            context,
            text="Ого! Здається, ти хочеш поговорити з кимось крутим! Зараз покажу тобі моїх друзів... 🗣✨"
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
        "Ой-ой! Здається, твої слова змило хвилею... 🌊 Я нічого не зрозумів! Спробуй щось із меню!",
        "Тартарський соус! 🍔 Це якесь таємне послання від Планктона? Краще обери команду!",
        "Гаррі каже, що це не схоже на команду... 🐌 Спробуй ще раз, друже!",
        "Ми з Патріком цілий день думали, але так і не зрозуміли, що це! ⭐️ Обирай кнопку!",
        "Це звучить так само дивно, як Сквідвард на вечірці! 🐙 Давай краще користуватися меню!",
        "Ух ти! Якесь незнайоме слово! Може, краще полювання на медуз? 🪼 Або просто обери команду!",
        "Мої бульбашки кажуть, що це не те... 🫧 Спробуй натиснути на /start!",
        "Ой! Ти так швидко говориш, що в мене штани затремтіли! 🩳 Давай за командами!",
    ]
    random_response = choice(funny_responses)
    available_commands = """
    🌟 Не знаєш з чого почати? Тисни /start!
    🧠 Або запитай Розумника через /gpt!
    """
    full_message = f"{random_response}\n{available_commands}"
    await update.message.reply_text(full_message)


async def translator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /translator command. Displays language selection for translation.
    """
    logger.info(f"Користувач {update.effective_user.id} відкрив режим перекладача")
    user_profile = context.user_data.get("user_profile")
    context.user_data.clear()
    context.user_data["user_profile"] = user_profile
    context.user_data["conversation_state"] = "translator"
    await send_image(update, context, "translator")

    buttons = {
        "translator_en": "English 🇺🇸",
        "translator_uk": "Українська 🇺🇦",
        "translator_ru": "Російська 🇷🇺",
        "start": "⬅️ Назад до Ананаса"
    }
    await send_text_buttons(update, context, "Ого! На яку мову мені перекласти твої слова? Обирай швидше! 🌐✨", buttons)


async def translator_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries for the translator mode.
    """
    query = update.callback_query
    await query.answer()
    data = query.data
    logger.info(f"Користувач {update.effective_user.id} вибрав мову або дію у перекладачі: {data}")

    if data == "start":
        user_profile = context.user_data.get("user_profile")
        context.user_data.clear()
        context.user_data["user_profile"] = user_profile
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
        await send_text(update, context, f"Є! Вибрано {context.user_data['translator_lang']} мову! 🌐 Тепер пиши свій текст, я чекаю!")


def _parse_number(text: str):
    text = text.strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def _decimals_in_input(text: str) -> int:
    """
    Returns how many digits user typed after decimal separator.
    Examples: "1,3" -> 1, "2.50" -> 2, "10" -> 0
    """
    s = text.strip().replace(",", ".")
    if "." not in s:
        return 0
    frac = s.split(".", 1)[1]
    digits = "".join(ch for ch in frac if ch.isdigit())
    return len(digits)


def _answers_match(user_answer: float, correct: float, raw_text: str) -> bool:
    """
    Smart check:
    - still accepts exact/very close answers
    - if user typed N decimals, accept if correct rounded to N decimals equals their number
    """
    if _is_close(user_answer, correct):
        return True

    n = _decimals_in_input(raw_text)
    if n > 0:
        return _is_close(user_answer, round(correct, n), eps=1e-12)

    return False


def _format_number(x: float) -> str:
    if abs(x - round(x)) < 1e-12:
        return str(int(round(x)))
    return str(x)


def _is_close(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps * max(1.0, abs(a), abs(b))

def _md_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace("_", "\\_")
            .replace("*", "\\*")
            .replace("`", "\\`")
            .replace("[", "\\[")
    )


async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Користувач {update.effective_user.id} відкрив калькулятор")
    user_profile = context.user_data.get("user_profile")
    context.user_data.clear()
    context.user_data["user_profile"] = user_profile
    context.user_data["conversation_state"] = "calc"
    context.user_data["calc_step"] = "first"
    name = user_profile["name"] if user_profile else ""
    await send_image(update, context, "calculator")
    await send_text(update, context, f"Я готовий! Я готовий! Давай порахуємо всі бульбашки в океані, {name}! 🧮🫧 Введи перше число:")


async def calc_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "calc_again":
        await calc(update, context)
        return

    if data.startswith("calc_op_"):
        op = data.replace("calc_op_", "", 1)

        if context.user_data.get("conversation_state") != "calc":
            await send_text(update, context, "Гей! Спочатку скажи мені /calc, щоб ми почали рахувати! 🧮")
            return

        if context.user_data.get("calc_step") != "op":
            await send_text(update, context, "Стривай! Спочатку введи перше число, а потім будемо вибирати дію! 🍍")
            return

        context.user_data["calc_op"] = op
        context.user_data["calc_step"] = "second"
        await send_text(update, context, "Супер-пупер! Ти молодець! 😃 А тепер введи друге число!")
        return