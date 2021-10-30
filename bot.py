from logging import log, WARNING, ERROR

import telebot
from telebot import apihelper
from pytils.translit import slugify

from avitoparser import Avito
from database_redis import Redis

from config import POXY_LOGIN, PROXY_IP, PROXY_PASS, PROXY_PORT, TELEGRAM_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

apihelper.proxy = {
    'https': f'socks5://{POXY_LOGIN}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}'
}

bot = telebot.TeleBot(TELEGRAM_TOKEN)

redis = Redis(REDIS_HOST, REDIS_PORT, REDIS_PASSWORD)
INPUT_DICT = {}


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(
        message.from_user.id,
        "/start - запуск ввода данных для поиска \n"
        "/parse - запуск парсинга после ввода/последний запрос юзера"
    )


@bot.message_handler(commands=['start'])
def send_start(message):
    bot.send_message(
        message.from_user.id,
        "Это парсер Авито. Заполните данные поиска. "
        "Обязательное поле - объект поиска. "
        "Необязательные - мин. цена, макс. цена, город, кол-во объявлений."
        " Минус(-) - пропустить необязательное поле. "
    )
    msg = bot.send_message(message.from_user.id, "Введите объект поиска")
    bot.register_next_step_handler(msg, process_search_step)


def process_search_step(message):
    try:
        search_object = str(message.text).strip()
        redis.connect().hmset(message.from_user.id, {"search_object": search_object})
        bot.send_message(
            message.from_user.id,
            'Примеры ввода: sankt-peterburg/санкт-петербург, '
            'rossiya/россия, moskva/москва'
        )
        msg = bot.reply_to(message, 'Введите город')
        bot.register_next_step_handler(msg, process_city_step)
    except Exception as e:
        log(level=ERROR, msg=e)
        bot.reply_to(e, 'ошибка')


def process_city_step(message):
    try:
        city = str(message.text).strip()
        if city == '-':
            city = ''
        redis.connect().hmset(message.from_user.id, {"city": slugify(city)})
        msg = bot.reply_to(message, 'мин. цена')
        bot.register_next_step_handler(msg, process_min_step)
    except Exception as e:
        log(level=ERROR, msg=e)
        bot.reply_to(e, 'ошибка')


def process_min_step(message):
    try:
        min_price = str(message.text).strip()
        if min_price == '-' or not str(min_price).isdigit():
            min_price = ''
        redis.connect().hmset(message.from_user.id, {"min_price": min_price})
        msg = bot.reply_to(message, 'макс. цена')
        bot.register_next_step_handler(msg, process_max_step)
    except Exception as e:
        log(level=ERROR, msg=e)
        bot.reply_to(e, 'ошибка')


def process_max_step(message):
    try:
        max_price = str(message.text).strip()
        if max_price == '-' or not str(max_price).isdigit():
            max_price = ''
        redis.connect().hmset(message.from_user.id, {"max_price": max_price})
        bot.send_message(
            message.from_user.id, 'Кол-во объявлений. Минус(-) - все объявления на странице'
        )
        msg = bot.reply_to(message, 'кол-во объявлений')
        bot.register_next_step_handler(msg, process_max_object_step)
    except Exception as e:
        log(level=ERROR, msg=e)
        bot.register_next_step_handler(e, 'ошибка')


def process_max_object_step(message):
    try:
        max_object = str(message.text).strip()
        if max_object == '-' or not str(max_object).isdigit():
            max_object = ''
        else:
            max_object = int(max_object)
        redis.connect().hmset(message.from_user.id, {"max_object": max_object})
        msg = bot.send_message(message.from_user.id, '/parse  -  начать парсинг')
        bot.register_next_step_handler(msg, send_parse_result)
    except Exception as e:
        log(level=ERROR, msg=e)
        bot.send_message(e, 'ошибка')


@bot.message_handler(commands=['parse'])
def send_parse_result(message):
    parse = Avito()
    try:
        redis.connect().hgetall(message.from_user.id)
    except KeyError as e:
        bot.send_message(message.from_user.id, 'Последний запрос не найден.')
        log(level=WARNING, msg=e)
        return
    input_dict = redis.connect().hgetall(message.from_user.id)
    result = parse.city(
        input_dict.get('city')
    ).min_price(
        input_dict.get('min_price')
    ).max_price(
        input_dict.get('max_price')
    ).search_object(
        input_dict.get('search_object')
    ).get().parse()
    limit = input_dict.get('max_object')
    limit = int(limit) if str(limit).isdigit() else None
    for res in result[:limit]:
        bot.send_message(message.from_user.id, ''.join(map(str, res)))


bot.infinity_polling(timeout=1000, long_polling_timeout=2000)