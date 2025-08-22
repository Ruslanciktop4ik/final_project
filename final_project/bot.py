import telebot
import sqlite3
import json
import os
from telebot import types

TOKEN = "8109746141:AAGN8QXEn614ZLDoZQJugLkiMeR8Dd4exhM"
bot = telebot.TeleBot(TOKEN)

# Список ID админов
ADMINS = [2069586509]  

# Загружаем FAQ
with open("faq.json", encoding="utf-8") as f:
    faq = json.load(f)

# ---------- БАЗА ДАННЫХ ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

init_db()

def save_request(user_id, username, message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, username, message) VALUES (?, ?, ?)",
        (user_id, username, message)
    )
    conn.commit()
    conn.close()

# ---------- КНОПКИ ----------
def main_menu(user_id):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    ask_btn = types.KeyboardButton("✍ Задать вопрос")
    keyboard.add(ask_btn)

    if user_id in ADMINS:  # Только админам
        admin_btn = types.KeyboardButton("🛠 Панель админа")
        keyboard.add(admin_btn)

    return keyboard

def admin_panel():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("📂 Посмотреть запросы", callback_data="admin_requests"))
    keyboard.add(types.InlineKeyboardButton("🗑 Очистить базу", callback_data="admin_clear"))
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back"))
    return keyboard

# ---------- КОМАНДЫ ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id, 
        "Привет! 👋 Я бот-помощник. Выберите действие:", 
        reply_markup=main_menu(message.from_user.id)
    )

# ---------- ОБРАБОТКА КНОПОК ----------
@bot.message_handler(func=lambda m: m.text == "✍ Задать вопрос")
def ask_question(message):
    bot.send_message(message.chat.id, "Введите ваш вопрос текстом или отправьте голосовое сообщение.")

@bot.message_handler(func=lambda m: m.text == "🛠 Панель админа")
def show_admin_panel(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "У вас нет прав для панели администратора.")
        return
    bot.send_message(message.chat.id, "Добро пожаловать в панель администратора:", reply_markup=admin_panel())

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_actions(call):
    if call.from_user.id not in ADMINS:
        bot.answer_callback_query(call.id, "Нет доступа")
        return

    if call.data == "admin_requests":
        send_requests_to_admin(call.message.chat.id)
    elif call.data == "admin_clear":
        clear_requests(call.message)
    elif call.data == "admin_back":
        bot.send_message(
            call.message.chat.id, 
            "Вы вернулись в главное меню:", 
            reply_markup=main_menu(call.from_user.id)
        )

# ---------- ЗАПРОСЫ ДЛЯ АДМИНОВ ----------
def send_requests_to_admin(chat_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, message, timestamp FROM requests ORDER BY timestamp DESC")
    requests = cursor.fetchall()
    conn.close()

    if not requests:
        bot.send_message(chat_id, "Нет новых запросов.")
        return

    for username, msg, ts in requests:
        if msg.startswith("Голосовое сообщение:"):
            file_path = msg.replace("Голосовое сообщение: ", "").strip()
            if os.path.exists(file_path):
                bot.send_message(chat_id, f"Запрос от @{username} ({ts}):")
                with open(file_path, "rb") as voice_file:
                    bot.send_voice(chat_id, voice_file)
            else:
                bot.send_message(chat_id, f"Запрос от @{username} ({ts}): файл голосового не найден.")
        else:
            bot.send_message(chat_id, f"Запрос от @{username} ({ts}): {msg}")

def clear_requests(message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM requests")
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "Все запросы успешно удалены из базы.")

# ---------- ТЕКСТ ----------
@bot.message_handler(content_types=["text"])
def handle_text(message):
    if message.text.startswith("/"):
        return  # команды отдельно обрабатываются

    user_text = message.text.strip()
    # Если вопрос есть в FAQ → отвечаем
    if user_text in faq:
        bot.send_message(message.chat.id, f"Ответ: {faq[user_text]}")
    else:
        # Если нет → сохраняем в базу
        save_request(message.from_user.id, message.from_user.username, user_text)
        bot.send_message(message.chat.id, "Извините, ответа на этот вопрос нет. Мы передадим его специалисту.")

# ---------- ГОЛОС ----------
@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    voice_dir = "voices"
    os.makedirs(voice_dir, exist_ok=True)
    file_path = os.path.join(voice_dir, f"{message.from_user.id}_{message.message_id}.ogg")
    with open(file_path, "wb") as f:
        f.write(downloaded_file)

    save_request(message.from_user.id, message.from_user.username, f"Голосовое сообщение: {file_path}")
    bot.send_message(message.chat.id, "Ваш голосовой вопрос сохранён. Специалист его прослушает.")

# ---------- СТАРТ ----------
bot.polling()