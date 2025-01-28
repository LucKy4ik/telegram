import g4f
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
import html

history_chat = {}
bot = telebot.TeleBot('7711898353:AAFYy2UEn9EXETPgEpGUgrdubIVgVqWKcuM') 
user_name = str()

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
        return f"Температура: {temperature}°C{emoji.emojize(':thermometer:')}, но ощущается как {weather_condition}°C.\nВетер: {wind}м/с.{emoji.emojize(':dashing_away:')}"   
    except AttributeError:
        conn = sqlite3.connect("users_telegram.sql")
        cur = conn.cursor()
        cur.execute('UPDATE users SET user_city = ? WHERE user_name = ?', (None, user_name))
        conn.commit()
        cur.close()
        conn.close()
        return "Город не найден, попробуйте установить его заново c помощью команды /weather"

def send_time():
    try:
        global user_name
        conn = sqlite3.connect("users_telegram.sql")
        cur = conn.cursor()
        cur.execute('SELECT *FROM users')
        users = cur.fetchall()
        for i in range(len(users)):
            bot.send_message(users[i][2], f"Доброе утро!{emoji.emojize(':sun:')}\nВремя вставать, сейчас 06:30.{emoji.emojize(':six-thirty:')}\n{weather(users[i][3], users[i][1]) if weather(users[i][3], users[i][1]) !=  "Город не найден, попробуйте установить его заново c помощью команды /weather" else 'Чтобы я смог оповещать вас о погоде, вам нужно зарегистрировать ваш город, с помощью команды\n/weather'}.\nЖелаю тебе удачного дня!{emoji.emojize(':four_leaf_clover:')}")
    except requests.exceptions.ConnectionError:
        for i in range(len(users)):
            bot.reply_to(users[i][2], "Ошибка: Не удалось установить соединение с сервером Telegram. Попробуйте позже.")
    finally:
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
    try:
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
        for i in users:
            print(i)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(telebot.types.KeyboardButton('/menu'), telebot.types.KeyboardButton('/help'))
        markup.add(telebot.types.KeyboardButton('/weather'))
        bot.send_message(message.chat.id, f"Привет!{emoji.emojize(':waving_hand:')}\nЯ Ваш виртуальный ассистент, готовый помочь Вам в любых вопросах{emoji.emojize(':robot:')}\nПросто напишите, что Вас интересует, и я с радостью предоставлю нужную информацию или выполню задачу{emoji.emojize(':memo:')}", reply_markup=markup)
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "Ошибка: Не удалось установить соединение с сервером Telegram. Попробуйте позже.")
    finally:
        cur.close()
        conn.close()



@bot.message_handler(commands=['menu'])
def menu(message):
    try:
        conn = sqlite3.connect("users_telegram.sql")
        cur = conn.cursor()
        cur.execute('SELECT *FROM users WHERE user_name = ?', (message.from_user.first_name,))
        user_data = cur.fetchone()
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row(telebot.types.InlineKeyboardButton('Узнать погоду', callback_data='weather'), telebot.types.InlineKeyboardButton('Задать вопрос', callback_data='question'))
        markup.row(telebot.types.InlineKeyboardButton('Открыть электронный дневник' if user_data[6] else 'Зарегистрировать электронный дневник', callback_data='diary'))
        bot.send_message(message.chat.id, f"{emoji.emojize(":glowing_star:")} Вы открыли меню-панель! {emoji.emojize(":glowing_star:")}\nДобро пожаловать в мир возможностей! Здесь Вы найдете разнообразные функции, которые помогут Вам максимально эффективно использовать все возможности нашего приложения. Исследуйте, настраивайте и наслаждайтесь удобством, которое предлагает меню. Ваши действия теперь под контролем!", reply_markup=markup)
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "Ошибка: Не удалось установить соединение с сервером Telegram. Попробуйте позже.")
    finally:
        cur.close()
        conn.close()
@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
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
            marks_info1 = str()
            marks_info2 = str()
            marks_info3 = str()
            marks_info4 = str()
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
            count = len(soup.select('div.DivForGradesTable th.grades-average-th'))
            for num in num_l:
                lesson_value = num.get('lesson')
                name_l = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_= 'grades-lesson').get_text()
                average_mark1 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')) else ''
                if average_mark1 != '':
                    marks_info1 += f"***{name_l}***:\nСредний балл: {average_mark1}\n{'-'*60}\n"
                average_mark2 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                if average_mark2 != '': 
                    marks_info2 += f"***{name_l}***:\nСредний балл: {average_mark2}\n{'-'*60}\n"
                if count == 3:
                    average_mark3 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark3 != '':    
                        marks_info3 += f"***{name_l}***:\nСредний балл: {average_mark3}\n{'-'*60}\n"
                elif count == 4:    
                    average_mark4 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark4 != '':
                        marks_info4 += f"***{name_l}***:\nСредний балл: {average_mark4}\n{'-'*60}\n"
            cur1.execute('UPDATE users_info_el SET mark_1 = ? WHERE user_name = ?', (marks_info1, callback.from_user.first_name))
            conn1.commit()
            cur1.execute('UPDATE users_info_el SET mark_2 = ? WHERE user_name = ?', (marks_info2, callback.from_user.first_name))
            conn1.commit()
            if count == 3:
                cur1.execute('UPDATE users_info_el SET mark_3 = ? WHERE user_name = ?', (marks_info3, callback.from_user.first_name)) 
                conn1.commit()
            elif count == 4:    
                cur1.execute('UPDATE users_info_el SET mark_4 = ? WHERE user_name = ?', (marks_info4, callback.from_user.first_name)) 
                conn1.commit()
            marks_info1 = str()
            marks_info2 = str()
            marks_info3 = str()
            marks_info4 = str()    
            for num in num_l:
                lesson_value = num.get('lesson')
                name_l = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_= 'grades-lesson').get_text()
                average_mark1 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')) else ''
                if average_mark1 != '':
                    marks_info1 += f"***{name_l}***({average_mark1}):\n"
                    for marks in soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_="grades-marks").find_all('span'):
                        marks_info1 += marks.get_text()
                    marks_info1 += f"\n{'-'*60}\n"
                average_mark2 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                if average_mark2 != '':
                    marks_info2 += f"***{name_l}***({average_mark2}):\n"
                    for marks in soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_="grades-marks").find_next('td', class_="grades-marks").find_all('span'):
                        marks_info2 += marks.get_text()
                    marks_info2 += f"\n{'-'*60}\n"
                if count == 3:
                    average_mark3 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark3 != '':
                        marks_info3 += f"***{name_l}***({average_mark3}):\n"
                        for marks in soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_="grades-marks").find_next('td', class_="grades-marks").find_all('span'):
                            marks_info3 += marks.get_text()
                elif count == 4:
                    average_mark4 = soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).get_text() if soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')).find_next('td', class_=re.compile(r'grades-average')) else ''
                    if average_mark4 != '':
                        marks_info4 += f"***{name_l}***({average_mark4}):\n"
                        for marks in soup.find('tr', {'lesson': f'{lesson_value}'}).find('td', class_="grades-marks").find_next('td', class_="grades-marks").find_all('span'):
                            marks_info4 += marks.get_text()
            cur1.execute('UPDATE users_info_el SET marks_1 = ? WHERE user_name = ?', (marks_info1, callback.from_user.first_name))
            conn1.commit()
            cur1.execute('UPDATE users_info_el SET marks_2 = ? WHERE user_name = ?', (marks_info2, callback.from_user.first_name))
            conn1.commit()
            if count == 3:
                cur1.execute('UPDATE users_info_el SET marks_3 = ? WHERE user_name = ?', (marks_info1, callback.from_user.first_name))
                conn1.commit()
            elif count == 4:
                cur1.execute('UPDATE users_info_el SET marks_4 = ? WHERE user_name = ?', (marks_info2, callback.from_user.first_name))
                conn1.commit()
            cur1.close()
            conn1.close()
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton('Табель', callback_data = 'report_card'))
            if count == 2:
                markup.row(telebot.types.InlineKeyboardButton('1 Полугодие', callback_data = 'first'), telebot.types.InlineKeyboardButton('2 Полугодие', callback_data = 'second'))  
            elif count == 3:
                markup.row(telebot.types.InlineKeyboardButton('1 Триместр', callback_data = 'first'), telebot.types.InlineKeyboardButton('2 Триместр', callback_data = 'second'))
                markup.row(telebot.types.InlineKeyboardButton('3 Триместр', callback_data = 'third'))
            else:
                markup.row(telebot.types.InlineKeyboardButton('1 Четверть', callback_data = 'first'), telebot.types.InlineKeyboardButton('2 Четверть', callback_data = 'second'))
                markup.row(telebot.types.InlineKeyboardButton('3 Четверть', callback_data = 'third'), telebot.types.InlineKeyboardButton('4 Четверть', callback_data = 'fourth'))
            markup.add(telebot.types.InlineKeyboardButton('Табель с оценками', callback_data = 'report_card'))
            if count == 2:
                markup.row(telebot.types.InlineKeyboardButton('1 Полугодие', callback_data = 'First'), telebot.types.InlineKeyboardButton('2 Полугодие', callback_data = 'Second'))  
            elif count == 3:
                markup.row(telebot.types.InlineKeyboardButton('1 Триместр', callback_data = 'First'), telebot.types.InlineKeyboardButton('2 Триместр', callback_data = 'Second'))
                markup.row(telebot.types.InlineKeyboardButton('3 Триместр', callback_data = 'Third'))
            else:
                markup.row(telebot.types.InlineKeyboardButton('1 Четверть', callback_data = 'First'), telebot.types.InlineKeyboardButton('2 Четверть', callback_data = 'Second'))
                markup.row(telebot.types.InlineKeyboardButton('3 Четверть', callback_data = 'Third'), telebot.types.InlineKeyboardButton('4 Четверть', callback_data = 'Fourth'))
            bot.send_message(callback.message.chat.id, f"{emoji.emojize(':crystal_ball:')}{emoji.emojize(':minus:')}{emoji.emojize(':sparkles:')}Главное меню{emoji.emojize(':sparkles:')}{emoji.emojize(':minus:')}{emoji.emojize(':crystal_ball:')}", reply_markup=markup)

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
                conn1 = sqlite3.connect("users_elshool.sql") 
                cur1 = conn1.cursor()
                cur1.execute('CREATE TABLE IF NOT EXISTS users_info_el (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name varchar(50), mark_1 TEXT, mark_2 TEXT, mark_3 TEXT, mark_4 TEXT, marks_1 TEXT, marks_2 TEXT, marks_3 TEXT, marks_4 TEXT)')
                conn1.commit()
                cur1.execute('SELECT COUNT(*) FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
                exists = cur1.fetchone()[0]
                if not exists:
                    cur1.execute('INSERT INTO users_info_el (user_name, mark_1, mark_2, mark_3, mark_4, marks_1, marks_2, marks_3, marks_4) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (callback.from_user.first_name, '', '', '', '', '', '', '', ''))
                    conn1.commit()
                cur1.close()
                conn1.close()
                bot.send_message(callback.message.chat.id, "Успешная авторизация!\nТеперь вы можете использовать данную функцию")
            except TypeError: 
                bot.send_message(callback.message.chat.id, "Авторизация не прошла.\nЗарегистрируйте свои данные с помощью команды /elschool, чтоб в будущем вы могли пользоваться данной функцией.")
    elif callback.data =='report_card':
        pass
    elif callback.data == 'first':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[2], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data == 'second':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[3], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data == 'third':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[4], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data == 'fourth':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[5], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data =='First':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[6], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data =='Second':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[7], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data =='Third':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[8], "Markdown")
        cur1.close()
        conn1.close()
    elif callback.data =='Fourth':
        conn1 = sqlite3.connect("users_elshool.sql") 
        cur1 = conn1.cursor()
        cur1.execute('SELECT *FROM users_info_el WHERE user_name = ?', (callback.from_user.first_name,))
        bot.send_message(callback.message.chat.id, cur1.fetchone()[9], "Markdown")
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
    try:
        conn = sqlite3.connect("users_telegram.sql")
        cur = conn.cursor()
        cur.execute('SELECT *FROM users WHERE user_name = ?', (message.from_user.first_name,))
        city = cur.fetchone()[3]
        if city is not None:
            bot.reply_to(message, weather(city, message.from_user.first_name))
        else:
            bot.reply_to(message, "Напишите ваш город:")
            bot.register_next_step_handler(message, user_city)
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "Ошибка: Не удалось установить соединение с сервером Telegram. Попробуйте позже.")
    finally:
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
    try:
        bot.send_message(message.chat.id, "Если у вас возникли какие-то вопросы, либо нашли ошибку бота, напишите сюда ->@LucKyy0_0")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "Ошибка: Не удалось установить соединение с сервером Telegram. Попробуйте позже.")

@bot.message_handler(content_types='text')
def i_message(message):
    try:
        if message.from_user.id not in history_chat:
            history_chat[message.from_user.id] = [{"role": "system", "content": "Пожалуйста, ответь на вопрос пользователя четко и понятно на русском."}]
        history_chat[message.from_user.id].append({"role": "user", "content": message.text.strip()})

        prompt = f"Пользователь спросил: '{message.text.strip()}'. Ответь четко и ясно на его вопрос на русском языке. Перед отправкой, проверь свой ответ, исправь ошибки, измени иностранные слова на русский."
        prompt += "\nИстория беседы:\n" + "\n".join([item["content"] for item in history_chat[message.from_user.id]])
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
            )
            if isinstance(response, dict) and 'choices' in response:
                    assistant_message = response['choices'][0]['message']['content']
            else:
                    assistant_message = str(response)
        except Exception as e:
            assistant_message = f"Произошла ошибка при генерации ответа. Напишите ваш вопрос точнее и проще. Отправьте данную ошибку( {e} ) сюда -> @LucKyy0_0"

        history_chat[message.from_user.id].append({"role": "assistant", "content": assistant_message})

        decoded_response = html.unescape(assistant_message)
        bot.reply_to(message, decoded_response, parse_mode="Markdown")
    except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, ConnectionResetError, telebot.apihelper.ApiTelegramException, ):
        bot.reply_to(message, "Ошибка: Не удалось установить соединение с сервером Telegram. Попробуйте позже.")


bot.polling(none_stop=True, timeout=60)