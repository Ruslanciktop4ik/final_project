import sqlite3
import json
# Подключение или создание базы данных
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Создание таблицы, если её нет
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



import json

# Загружаем FAQ из файла
with open("faq.json", encoding="utf-8") as f:
    faq = json.load(f)

while True:
    user_question = input("Введите вопрос (или 'завершить' для завершения): ").strip()
    if user_question.lower() == "завершить":
        break
#если вопрос есть в FAQ то даем ответ
    if user_question in faq:
        print("Ответ:", faq[user_question])
    else:
        print("Извините, ответа на этот вопрос нет.") #скоро будем сохранять в бд и администротор будет смотреть


        #да и скоро будет тг бот