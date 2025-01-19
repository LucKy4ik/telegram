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
import re

client = Client()
history_chat = {}
bot = telebot.TeleBot('7711898353:AAFYy2UEn9EXETPgEpGUgrdubIVgVqWKcuM') 

async def translator1(n_city):
    translator = Translator()
    result = await translator.translate(f"{n_city} (город)", dest='en')
    return result.text.replace(' (city)', '')

def weather(user_city, user_name):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"
            }
        response = requests.get(f"https://yandex.ru/weather/{asyncio.run(translator1(user_city)).lower()}", headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        # Извлечение данных о погоде
        temperature = soup.find("div", class_="temp fact__temp fact__temp_size_s").find("span", class_="temp__value temp__value_with-unit").get_text()
        weather_condition = soup.find("div", class_="link__feelings fact__feelings").find("span", class_="temp__value temp__value_with-unit").get_text()
        #humidity = soup.find("div", class_="term term_orient_v fact__humidity").find("span", class_="a11y-hidden").get_text()
        wind = soup.find("div", class_="term term_orient_v fact__wind-speed").find("span", class_="wind-speed").get_text()
        return f"Температура: {temperature}°C{emoji.emojize(':thermometer:')}, но ощущается как {weather_condition}°C{emoji.emojize(':face_with_rolling_eyes:')}.\nВетер: {wind}м/с.{emoji.emojize(':dashing_away:')}"   
    except AttributeError:
        conn = sqlite3.connect("users_telegram.sql")
        cur = conn.cursor()
        cur.execute('UPDATE users SET user_city = ? WHERE user_name = ?', (None, user_name))
        conn.commit()
        cur.close()
        conn.close()
        return "Город не найден, попробуйте установить его заново c помощью команды /weather"

def send_time():
    global user_name
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()
    cur.execute('SELECT *FROM users')
    users = cur.fetchall()
    for i in range(len(users)):
        bot.send_message(users[i][2], f"Доброе утро!{emoji.emojize(':sun:')}\nВремя вставать, сейчас 6:30.{emoji.emojize(':six-thirty:')}\n{weather(users[i][3], users[i][1]) if weather(users[i][3], users[i][1]) !=  "Город не найден, попробуйте установить его заново c помощью команды /weather" else 'Чтобы я смог оповещать вас о погоде, вам нужно зарегистрировать ваш город, с помощью команды\n/weather'}.\nЖелаю тебе удачного дня!{emoji.emojize(':four_leaf_clover:')} Не забудь про сегодняшние планы!")
    cur.close()
    conn.close()
def run_time():
    schedule.every().day.at("06:30").do(send_time) #Запланирование действия
    while True:
        schedule.run_pending()
        time.sleep(10)
threading.Thread(target=run_time).start() #Параллельный поток

@bot.message_handler(commands=['start'])
def start(message):
    global user_name
    user_name = message.from_user.first_name

    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name varchar(50), message_id varchar(50), user_city varchar(50), user_login varchar(50), user_password varchar(50), user_url_el varchar(50))')
    conn.commit()

    cur.execute('SELECT COUNT(*) FROM users WHERE user_name = ?', (message.from_user.first_name,))
    exists = cur.fetchone()[0]
    if not exists:
        cur.execute('INSERT INTO users(user_name, message_id, user_city, user_login, user_password, user_url_el) VALUES (?, ?, ?, ?, ?, ?)', (message.from_user.first_name, message.chat.id, None, None, None, None))
        conn.commit()
    cur.execute('SELECT *FROM users')
    users = cur.fetchall()
    print(users) 
    cur.close()
    conn.close()

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton('/menu'), telebot.types.KeyboardButton('/help'))
    markup.add(telebot.types.KeyboardButton('/weather'))
    bot.send_message(message.chat.id, f"Привет!{emoji.emojize(':waving_hand:')}\nЯ Ваш виртуальный ассистент, готовый помочь Вам в любых вопросах{emoji.emojize(':robot:')}\nПросто напишите, что Вас интересует, и я с радостью предоставлю нужную информацию или выполню задачу{emoji.emojize(':memo:')}", reply_markup=markup)


@bot.message_handler(commands=['menu'])
def menu(message):
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()
    cur.execute('SELECT *FROM users WHERE user_name = ?', (message.from_user.first_name,))
    user_data = cur.fetchone()
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton('Узнать погоду', callback_data='weather'), telebot.types.InlineKeyboardButton('Задать вопрос', callback_data='question'))
    markup.row(telebot.types.InlineKeyboardButton('Открыть электронный дневник' if user_data[6] else 'Зарегистрировать электронный дневник', callback_data='diary'))
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, f"{emoji.emojize(":glowing_star:")} Вы открыли меню-панель! {emoji.emojize(":glowing_star:")}\nДобро пожаловать в мир возможностей! Здесь Вы найдете разнообразные функции, которые помогут Вам максимально эффективно использовать все возможности нашего приложения. Исследуйте, настраивайте и наслаждайтесь удобством, которое предлагает меню. Ваши действия теперь под контролем!", reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    marks_info = str()
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()
    cur.execute('SELECT *FROM users WHERE user_name = ?', (callback.from_user.first_name,))
    user_data = cur.fetchone()
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 YaBrowser/24.12.0.0 Safari/537.36"
            } 
    if callback.data == 'weather':
        bot.send_message(callback.message.chat.id, weather(user_data[3], callback.from_user.first_name))
    elif callback.data == 'question':
        bot.send_message(callback.message.chat.id, "Привет!\nВы можете задать любой вопрос нашему телеграмм-боту.\nПожалуйста, убедитесь, что Ваш вопрос сформулирован чётко и корректно, чтобы вы смогли быстрее и точнее получить ответ.\nЖдём Ваши Вопросы!")
    elif callback.data == 'diary':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        if user_data[6] is not None:
            try:
                login_url = 'https://elschool.ru/logon/index' #URL для авторизации
                credentials = { #Учетные данные
                    'login': f'{user_data[4]}',
                    'password': f'{user_data[5]}'
                    }
                session = requests.Session()
                session.headers.update(headers)
                session.post(login_url, data=credentials)

                user_data_url = 'https://elschool.ru/users/privateoffice'
                user_data_response = session.get(user_data_url, headers=headers)
                        
                conn1 = sqlite3.connect("users_elshool.sql") 
                cur1 = conn1.cursor()
                cur1.execute('CREATE TABLE IF NOT EXISTS users_info_el (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name varchar(50), mark_1 TEXT, mark_2 TEXT, mark_3 TEXT, mark_4 TEXT, marks_1 TEXT, marks_2 TEXT, marks_3 TEXT, marks_4 TEXT)')
                conn1.commit()
                cur1.execute('SELECT COUNT(*) FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
                exists = cur1.fetchone()[0]
                if not exists:
                    cur1.execute('INSERT INTO users_info_el (user_name, mark_1, mark_2, mark_3, mark_4, marks_1, marks_2, marks_3, marks_4) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (callback.from_user.first_name, '', '', '', '', '', '', '', ''))
                    conn1.commit()
                user_grades_response = session.get(user_data[6], headers=headers)
                soup = BeautifulSoup(user_grades_response.text, 'html.parser')
                num_l = soup.find('tbody').find_all('tr')
                for num in num_l:
                    lesson_value = num.get('lesson')
                    name_l = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_= 'grades-lesson').get_text()
                    average_mark = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark != '':
                        marks_info += f"***{name_l}***:\nСредний балл: {average_mark}\n{'-'*60}\n"
                cur1.execute('UPDATE users_info_el SET mark_1 = ? WHERE user_name = ?', (marks_info, callback.from_user.first_name))
                conn1.commit()
                marks_info = str()    
                for num in num_l:
                    lesson_value = num.get('lesson')
                    name_l = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_= 'grades-lesson').get_text()
                    average_mark = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark != '':
                        marks_info += f"***{name_l}***:\nСредний балл: {average_mark}\n{'-'*60}\n"
                cur1.execute('UPDATE users_info_el SET mark_2 = ? WHERE user_name = ?', (marks_info, callback.from_user.first_name))
                conn1.commit()
                marks_info = str()
                for num in num_l:
                    lesson_value = num.get('lesson')
                    name_l = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_= 'grades-lesson').get_text()
                    average_mark = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark:
                        marks_info += f"***{name_l}***({average_mark}):\n"
                        for marks in soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_="grades-marks").find_all('span'):
                            marks_info += marks.get_text()
                        marks_info += f"\n{'-'*60}\n"
                cur1.execute('UPDATE users_info_el SET marks_1 = ? WHERE user_name = ?', (marks_info, callback.from_user.first_name))
                conn1.commit()
                marks_info = str()
                for num in num_l:
                    lesson_value = num.get('lesson')
                    name_l = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_= 'grades-lesson').get_text()
                    average_mark = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark:
                        marks_info += f"***{name_l}***({average_mark}):\n"
                        for marks in soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_="grades-marks").find_next('td', class_="grades-marks").find_all('span'):
                            marks_info += marks.get_text()
                        marks_info += f"\n{'-'*60}\n"
                cur1.execute('UPDATE users_info_el SET marks_2 = ? WHERE user_name = ?', (marks_info, callback.from_user.first_name))
                conn1.commit()
                cur1.close()
                conn1.close()
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton('Табель', callback_data = 'report_card'))
                markup.row(telebot.types.InlineKeyboardButton('1 Полугодие', callback_data = 'first_half_a_year'), telebot.types.InlineKeyboardButton('2 Полугодие', callback_data = 'second_half_a_year'))
                markup.add(telebot.types.InlineKeyboardButton('Табель с оценками', callback_data = 'report_card'))
                markup.add(telebot.types.InlineKeyboardButton('1 Полугодие', callback_data = 'First_half_a_year'), telebot.types.InlineKeyboardButton('2 Полугодие', callback_data = 'Second_half_a_year'))
                bot.send_message(callback.message.chat.id, f"{emoji.emojize(':crystal_ball:')}{emoji.emojize(':minus:')}{emoji.emojize(':sparkles:')}Главное меню{emoji.emojize(':sparkles:')}{emoji.emojize(':minus:')}{emoji.emojize(':crystal_ball:')}", reply_markup=markup)
            except AttributeError:
                bot.send_message(callback.message.chat.id, 'Неверный логин/пароль. Зарегистрируйте свои данные с помощью команды /elschool, чтоб в будущем вы могли пользоваться данной функцией.')
                conn = sqlite3.connect("users_telegram.sql")
                cur = conn.cursor()
                cur.execute('UPDATE users SET user_url_el = ? WHERE user_name = ?', (None, callback.from_user.first_name))
                conn.commit()

        else:
            try:
                login_url = 'https://elschool.ru/logon/index' #URL для авторизации
                credentials = { #Учетные данные
                    'login': f'{user_data[4]}',
                    'password': f'{user_data[5]}'
                    }
                session = requests.Session()
                session.headers.update(headers)
                session.post(login_url, data=credentials)

                user_data_url = 'https://elschool.ru/users/privateoffice'
                user_data_response = session.get(user_data_url, headers=headers)
                        
                soup = BeautifulSoup(user_data_response.text, 'html.parser')
                diary = soup.find('a', class_="d-block")
                href_value = diary['href']
                cur.execute('UPDATE users SET user_url_el = ? WHERE user_name = ?', (f'https://elschool.ru/users/diaries/grades?rooId={href_value[11:href_value.find('/s', 11)]}&instituteId={href_value[href_value.find('/s') + 9:href_value.find('/c', 20)]}&departmentId={href_value[href_value.find('/classes/') + 9: ]}&pupilId={soup.find('td', class_='personal-data__info-value personal-data__info-value_bold').get_text()}', callback.from_user.first_name))
                conn.commit()
                bot.send_message(callback.message.chat.id, "Успешная авторизация!\nТеперь вы можете использовать данную функцию")
            except TypeError: 
                bot.send_message(callback.message.chat.id, "Авторизация не прошла.\nЗарегистрируйте свои данные с помощью команды /elschool, чтоб в будущем вы могли пользоваться данной функцией.")
    elif callback.data =='report_card':
        bot.send_message(callback.message.chat.id, 'Выберите полугодие')
    elif callback.data == 'first_half_a_year':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[2], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data == 'second_half_a_year':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[3], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data =='First_half_a_year':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[6], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data =='Second_half_a_year':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[7], "Markdown")
        cur1.close()
        conn1.close()    
    cur.close()
    conn.close()

@bot.message_handler(commands=['elschool'])
def reg_elshool(message):
    bot.send_message(message.chat.id, "Напишите ваш логин:")
    bot.register_next_step_handler(message, reg_login)

def reg_login(message):
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()
    cur.execute('UPDATE users SET user_login = ? WHERE user_name = ?', (message.text, message.from_user.first_name))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, "Напишите ваш пароль:")
    bot.register_next_step_handler(message, reg_pass)

def reg_pass(message):
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()
    cur.execute('UPDATE users SET user_password = ? WHERE user_name = ?', (message.text, message.from_user.first_name))
    conn.commit()
    bot.send_message(message.chat.id, "Данные успешно сохранены.")
    cur.close()
    conn.close()

@bot.message_handler(commands=['weather'])
def weather_city(message):
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()
    cur.execute('SELECT *FROM users WHERE user_name = ?', (message.from_user.first_name,))
    city = cur.fetchone()[3]
    if city is not None:
        bot.reply_to(message, weather(city, message.from_user.first_name))
        cur.close()
        conn.close()
    else:
        bot.reply_to(message, "Напишите ваш город:")
        bot.register_next_step_handler(message, user_city)
        cur.close()
        conn.close()

def user_city(message):
    conn = sqlite3.connect("users_telegram.sql")
    cur = conn.cursor()

    cur.execute('UPDATE users SET user_city = ? WHERE user_name = ?', (message.text, message.from_user.first_name)) #city = message.text
    conn.commit()
    bot.send_message(message.chat.id, "Город сохранен")
    cur.close()
    conn.close()


@bot.message_handler(commands=['help'])
def information(message):
    bot.send_message(message.chat.id, "Если у вас возникли какие-то вопросы, либо нашли ошибку бота, напишите сюда ->@LucKyy0_0")

@bot.message_handler(content_types='text')
def i_message(message):
    user_text = message.text.strip()
    user_id = message.from_user.id
    if len(history_chat) >= 5:
        history_chat[user_id] = [{"role": "system", "content": "Пожалуйста, ответь на вопрос пользователя четко и понятно на русском."}]
    if user_id not in history_chat:
        history_chat[user_id] = [{"role": "system", "content": "Пожалуйста, ответь на вопрос пользователя четко и понятно на русском."}]
    history_chat[user_id].append({"role": "user", "content": user_text})

    prompt = f'Пользователь спросил: \'{user_text}\'. Ответь четко и ясно на его вопрос на русском. Если текст тебе не понятен или он не имеет смысловой и логической нагрузки, сообщи об этом пользователю.' 
    prompt += '\n Истрия беседы:\n' +'\n'.join([item["content"] for item in history_chat[user_id]])
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        gpt_response = response.choices[0].message.content
        history_chat[user_id].append({"role": "assistant", "content": gpt_response})
        bot.reply_to(message, gpt_response, parse_mode="Markdown")
    except requests.exceptions.ReadTimeout:
        gpt_response = None
    except Exception as e:
        bot.reply_to(message, "Произошла проблема с генерацией ответа.\nПопробуйте написать вопрос проще и понятнее!")
bot.polling(none_stop=True)