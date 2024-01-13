from datetime import timedelta
import telebot
import requests
from telebot import types
import json
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))

API = '5f11ae1f44349681d43e4a87f565e906'

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Сегодня", callback_data='today')
    markup.row(btn1)
    btn2 = types.InlineKeyboardButton("Завтра",callback_data='tomorrow')
    markup.row(btn2)
    btn3 = types.InlineKeyboardButton("На 5 дней", callback_data='5_days')
    markup.row(btn3)
    bot.send_message(message.chat.id, 'Приветствую, на какой день вас интересует прогноз погоды?', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def handle_message(message):
    if message.text == "Сегодня":
        get_weather_today(message)
    elif message.text == "Завтра":
        get_weather_for_tomorrow(message)
    elif message.text == "На 5 дней":
        get_weather_5_days_request(message)


def get_weather_today(message):
    msg = bot.send_message(message.chat.id, 'Напишите название города')
    bot.register_next_step_handler(msg, get_weather)


def get_weather_5_days_request(message):
    msg = bot.send_message(message.chat.id, 'Напишите название города')
    bot.register_next_step_handler(msg, get_weather_5_days)


def get_weather_for_tomorrow(message):
    msg = bot.send_message(message.chat.id, 'Напишите название города')
    bot.register_next_step_handler(msg, get_weather_tomorrow)


@bot.message_handler(func=lambda message: message.text.lower() == "сегодня", content_types=['text'])
def get_weather(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?&q={city}&appid={API}&units=metric&lang=ru')
    if res.status_code == 200:
        data = json.loads(res.text)
        temp = data["main"]["temp"]
        feel_temp = data["main"]["feels_like"]
        des = data['weather'][0]['description']
        bot.reply_to(message, f'На улице {des}, температура {temp}°C, ощущается как {feel_temp}°C.')
        if 'облачно с прояснениями' in des or 'небольшая облачность' in des:
            image_path = 'foggy-day.png'  # Путь к изображению
            image = open(image_path, 'rb')
            bot.send_photo(message.chat.id, image)
        elif 'пасмурно' in des or 'переменная облачность' in des:
            image_path = 'cloudy-day.png'
            image = open(image_path, 'rb')
            bot.send_photo(message.chat.id, image)
        elif 'дождь' in des:
            image_path = 'rain-drops.png'
            image = open(image_path, 'rb')
            bot.send_photo(message.chat.id, image)
        elif 'ясно' in des:
            image_path = 'sun.png'
            image = open(image_path, 'rb')
            bot.send_photo(message.chat.id, image)
        elif 'небольшой снег' in des:
            image_path = 'snowfall.png'
            image = open(image_path, 'rb')
            bot.send_photo(message.chat.id, image)
    else:
        bot.reply_to(message, 'Не удалось получить данные о погоде. Проверьте название города.')


@bot.message_handler(func=lambda message: message.text.lower() == "Завтра", content_types=['text'])
def get_weather_tomorrow(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?&q={city}&appid={API}&units=metric&lang=ru')
    if res.status_code == 200:
        data = json.loads(res.text)
        forecast = data['list']

        # Получение даты и времени сейчас и добавление дня для получения даты на следующий день
        today = datetime.utcnow()
        tomorrow = today + timedelta(days=1)
        tomorrow_date_str = tomorrow.strftime('%Y-%m-%d')

        # Переменные для хранения макс. и мин. температуры и описания погоды
        temp_max = None
        temp_min = None
        descriptions = []

        for entry in forecast:
            # Преобразуем timestamp в дату и проверяем, соответствует ли она завтрашней
            timestamp = entry['dt']
            forecast_date_str = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')

            if forecast_date_str == tomorrow_date_str:
                # Если та же дата, что и завтра, обновляем макс. и мин. температуру и собираем описания
                if (temp_max is None) or (entry['main']['temp_max'] > temp_max):
                    temp_max = entry['main']['temp_max']

                if (temp_min is None) or (entry['main']['temp_min'] < temp_min):
                    temp_min = entry['main']['temp_min']

                descriptions.append(entry['weather'][0]['description'])

        # Если прогноз на завтра найден, отправляем его пользователю
        if descriptions:
            # Обычно берется наиболее частое описание за день
            most_common_description = max(set(descriptions), key=descriptions.count)

            bot.send_message(
                message.chat.id,
                f'Прогноз погоды на завтра {tomorrow_date_str}:\n' +
                f'На улице будет {most_common_description.capitalize()},\n' +
                f'Максимальная температура: {temp_max}°C\n' +
                f'Минимальная температура: {temp_min}°C'
            )
            if 'облачно с прояснениями' in most_common_description or 'небольшая облачность' in most_common_description:
                image_path = 'foggy-day.png'  # Путь к изображению
                image = open(image_path, 'rb')
                bot.send_photo(message.chat.id, image)
            elif 'пасмурно' in most_common_description or 'переменная облачность' in most_common_description:
                image_path = 'cloudy-day.png'
                image = open(image_path, 'rb')
                bot.send_photo(message.chat.id, image)
            elif 'дождь' in most_common_description:
                image_path = 'rain-drops.png'
                image = open(image_path, 'rb')
                bot.send_photo(message.chat.id, image)
            elif 'ясно' in most_common_description:
                image_path = 'sun.png'
                image = open(image_path, 'rb')
                bot.send_photo(message.chat.id, image)
            elif 'небольшой снег' in most_common_description:
                image_path = 'snowfall.png'
                image = open(image_path, 'rb')
                bot.send_photo(message.chat.id, image)
        else:
            bot.send_message(message.chat.id, 'Прогноз на завтра недоступен.')
    else:
        bot.reply_to(message, 'Не удалось получить данные о погоде. Проверьте название города.')


@bot.message_handler(func=lambda message: message.text.lower() == "на 5 дней", content_types=['text'])
def get_weather_5_days(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/forecast?&q={city}&appid={API}&units=metric&lang=ru')
    if res.status_code == 200:
        data = json.loads(res.text)
        forecast = data['list']
        daily_forecast = {}

        for entry in forecast:
            date = datetime.utcfromtimestamp(entry['dt']).strftime('%Y-%m-%d')
            temp_max = entry['main']['temp_max']
            temp_min = entry['main']['temp_min']
            description = entry['weather'][0]['description']

            if date not in daily_forecast:
                daily_forecast[date] = {
                    'max_temp': temp_max,
                    'min_temp': temp_min,
                    'descriptions': [description]
                }
            else:
                daily_forecast[date]['max_temp'] = max(daily_forecast[date]['max_temp'], temp_max)
                daily_forecast[date]['min_temp'] = min(daily_forecast[date]['min_temp'], temp_min)
                daily_forecast[date]['descriptions'].append(description)

        for date, weather_info in daily_forecast.items():
            # Находим самое частое описание погоды
            most_common_description = max(set(weather_info['descriptions']), key=weather_info['descriptions'].count)
            bot.send_message(
                message.chat.id,
                f'Прогноз погоды на {date}:\n' +
                f'На улице будет {most_common_description.capitalize()},\n' +
                f'Максимальная температура: {weather_info["max_temp"]}°C\n' +
                f'Минимальная температура: {weather_info["min_temp"]}°C'
            )
    else:
        bot.reply_to(message, 'Не удалось получить данные о погоде. Проверьте название города.')
bot.polling(none_stop=True)
