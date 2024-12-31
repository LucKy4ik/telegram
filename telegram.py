from g4f.client import Client
import telebot 
import requests
from bs4 import BeautifulSoup
import schedule
import threading
import time

message_id = None
city = None
#Погода----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def weather(user_city):
    global city
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"
            }
        response = requests.get(f"https://yandex.ru/pogoda/{user_city.lower()}", headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        # Извлечение данных о погоде
        pogoda = soup.find("div", class_="fact__temp-wrap").find("a",{'aria-label': True}).get_text()
        temperature = soup.find("div", class_="temp fact__temp fact__temp_size_s").get_text()
        weather_condition = soup.find("div", class_="link__feelings fact__feelings").find("div", class_="link__condition day-anchor i-bem").get_text()
        humidity = soup.find("div", class_="term term_orient_v fact__humidity").find("span", class_="a11y-hidden").get_text()
        wind = soup.find("div", class_="fact__props").find("span", class_="wind-speed").get_text()
        weather_city = f"Температура в {user_city}: {temperature}°C; " +  pogoda[pogoda.index("Ощущается"):].replace("как", "") + "°C\n" + f"Состояние погоды: {weather_condition.strip()}\n" + humidity + "\n" + f"Ветер: {wind}"
        return weather_city
    except AttributeError:
        city = None
        return "Город не найден, попробуйте ввести его снова"
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#Будильник------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def send_time():
    bot.send_message(message_id, "Wake up!")
def run_time():
    schedule.every().day.at("06:30").do(send_time)
    while True:
        schedule.run_pending()
        time.sleep(1)
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
client = Client()
history_chat = {}
bot = telebot.TeleBot('7711898353:AAEU0fXGwCRh1sOHWGrvrF-ILsW-3OySvxU') #
threading.Thread(target=run_time).start() #Параллельный поток

@bot.message_handler(commands=['start'])
def start(message):
    global message_id
    message_id = message.chat.id
    bot.send_message(message.chat.id, "Привет, можешь написать свой вопрос и я попробую ответить на него:")


@bot.message_handler(commands=['weather'])
def weather_city(message):
    if city is not None:
        bot.send_message(message.chat.id, weather(city))
    else:
        bot.send_message(message.chat.id, "Напишите ваш город:")
        bot.register_next_step_handler(message, user_city)

def user_city(message):
    global city
    city = message.text.lower()
    bot.send_message(message.chat.id, "Город сохранен")


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