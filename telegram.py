from g4f.client import Client
import telebot 
import requests
from bs4 import BeautifulSoup
import schedule
import threading
import time
import sqlite3
from googletrans import Translator
import asyncio
import emoji

message_id = None
city = None
user_name = None

async def translator1(n_city):
    translator = Translator()
    result = await translator.translate(f"{n_city} (город)", dest='en')
    return result.text.replace(' (city)', '')

def weather(user_city):
    global city
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"
            }
        response = requests.get(f"https://yandex.ru/weather/{asyncio.run(translator1(user_city)).lower()}", headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        # Извлечение данных о погоде
        temperature = soup.find("div", class_="temp fact__temp fact__temp_size_s").find("span", class_="temp__value temp__value_with-unit").get_text()
        weather_condition = soup.find("div", class_="link__feelings fact__feelings").find("span", class_="temp__value temp__value_with-unit").get_text()
        humidity = soup.find("div", class_="term term_orient_v fact__humidity").find("span", class_="a11y-hidden").get_text()
        wind = soup.find("div", class_="term term_orient_v fact__wind-speed").find("span", class_="wind-speed").get_text()
        return f"Температура: {temperature}°C{emoji.emojize(':thermometer:')}, но ощущается как: {weather_condition}°C{emoji.emojize(':face_with_rolling_eyes:')}.\n{humidity}\nВетер: {wind}м/с.{emoji.emojize(':dashing_away:')}"   
    except AttributeError:
        print("Ошибка")
        city = None
        conn = sqlite3.connect("user_telegram.sql")
        cur = conn.cursor()
        cur.execute('UPDATE users SET user_city = ? WHERE user_name = ?', (city, user_name))
        conn.commit()
        cur.close()
        conn.close()
        return "Город не найден, попробуйте ввести его снова"

def send_time():
    bot.send_message(message_id, f"Доброе утро!{emoji.emojize(':sun:')}\nВремя вставать, сейчас 6:30.{emoji.emojize(':six-thirty:')}\nЗа окном {weather(city)}.\nЖелаю тебе удачного дня!{emoji.emojize(':four_leaf_clover:')} Не забудь про сегодняшние планы: None")
def run_time():
    schedule.every().day.at("06:30").do(send_time) #Запланирование действия
    while True:
        schedule.run_pending()
        time.sleep(1)
client = Client()
history_chat = {}
bot = telebot.TeleBot('7711898353:AAEU0fXGwCRh1sOHWGrvrF-ILsW-3OySvxU') #
threading.Thread(target=run_time).start() #Параллельный поток

@bot.message_handler(commands=['start'])
def start(message):
    global message_id
    global user_name
    message_id = message.chat.id
    user_name = message.from_user.first_name

    conn = sqlite3.connect("user_telegram.sql")
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name varchar(50), user_city varchar(50))')
    conn.commit()

    cur.execute('SELECT COUNT(*) FROM users WHERE user_name = ?', (message.from_user.first_name,))
    exists = cur.fetchone()[0]
    if not exists:
        cur.execute('INSERT INTO users(user_name, user_city) VALUES (?, ?)', (message.from_user.first_name, city))
        conn.commit()

    cur.execute('SELECT *FROM users')
    users = cur.fetchall()
    print(users) 
    info = ''
    for i in users:
        info += f'Имя: {i[1]}, city: {i[2]}\n'
        print(info)
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, f"Привет!{emoji.emojize(':waving_hand:')}\nЯ Ваш виртуальный ассистент, готовый помочь Вам в любых вопросах{emoji.emojize(':robot:')}\nПросто напишите, что Вас интересует, и я с радостью предоставлю нужную информацию или выполню задачу{emoji.emojize(':memo:')}")


@bot.message_handler(commands=['weather'])
def weather_city(message):
    conn = sqlite3.connect("user_telegram.sql")
    cur = conn.cursor()
    cur.execute('SELECT *FROM users WHERE user_name = ?', (message.from_user.first_name,))
    city = cur.fetchone()[2]
    if city is not None:
        bot.send_message(message.chat.id, weather(city))
    else:
        bot.send_message(message.chat.id, "Напишите ваш город:")
        bot.register_next_step_handler(message, user_city)

def user_city(message):
    global city
    city = message.text
    conn = sqlite3.connect("user_telegram.sql")
    cur = conn.cursor()

    cur.execute('UPDATE users SET user_city = ? WHERE user_name = ?', (city, message.from_user.first_name))
    conn.commit()
    bot.send_message(message.chat.id, "Город сохранен")
    cur.execute('SELECT *FROM users')
    users = cur.fetchall()
    info = ''
    for i in users:
        info += f'Имя: {i[1]}, city: {i[2]}\n'
    print(info)
    cur.close()
    conn.close()


@bot.message_handler(commands=['help'])
def information(message):
    bot.send_message(message.chat.id, "Если у вас возникли какие-то вопросы, либо нашли ошибку бота, напишите сюда ->@LucKyy0_0")

@bot.message_handler(content_types='text')
def i_message(message):
    user_text = message.text
    user_id = message.from_user.id

    if user_id not in history_chat:
        history_chat[user_id] = []

    history_chat[user_id].append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=history_chat[user_id]
    )

    gpt_response = response.choices[0].message.content
    bot.send_message(message.chat.id, gpt_response, "Markdown")

    history_chat[user_id].append({"role": "assistant", "content": gpt_response})

bot.polling(none_stop=True)