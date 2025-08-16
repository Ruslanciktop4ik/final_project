import telebot
import sqlite3
import json
import os

TOKEN = "8109746141:AAGN8QXEn614ZLDoZQJugLkiMeR8Dd4exhM"  # вставь сюда токен
bot = telebot.TeleBot(TOKEN)

# Список ID админов
ADMINS = [2069586509]  # <-- вставь сюда свои ID админов

# Загружаем FAQ
with open("faq.json", encoding="utf-8") as f:
    faq = json.load(f)

# Инициализация базы данных
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

# Сохранение запроса в базу
def save_request(user_id, username, message):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, username, message) VALUES (?, ?, ?)",
        (user_id, username, message)
    )
    conn.commit()
    conn.close()

# Команда для получения ID (удобно для админов)
@bot.message_handler(commands=["getid"])
def get_id(message):
    bot.send_message(message.chat.id, f"Твой ID: {message.from_user.id}")

# Команда для отправки запросов админам
@bot.message_handler(commands=["requests"])
def send_requests_command(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "У вас нет прав для этой команды.")
        return
    send_requests_to_admin(message.chat.id)

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

# Команда для очистки базы запросов
@bot.message_handler(commands=["clear_requests"])
def clear_requests(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "У вас нет прав для этой команды.")
        return

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM requests")
    conn.commit()
    conn.close()

    bot.send_message(message.chat.id, "Все запросы успешно удалены из базы.")

# Обработка текстовых сообщений
@bot.message_handler(content_types=["text"])
def handle_text(message):
    # Игнорируем команды (кроме /requests и /clear_requests), чтобы не сохранять их как обычные сообщения
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Неизвестная команда или недостаточно прав.")
        return

    user_text = message.text.strip()
    if user_text in faq:
        bot.send_message(message.chat.id, f"Ответ: {faq[user_text]}")
    else:
        save_request(message.from_user.id, message.from_user.username, user_text)
        bot.send_message(message.chat.id, "Извините, ответа на этот вопрос нет. Мы передадим его специалисту.")

# Обработка голосовых сообщений
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

bot.polling()

        