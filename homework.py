import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия токенов."""
    if not PRACTICUM_TOKEN:
        logging.critical('Отсутствует токен PRACTICUM_TOKEN')
        sys.exit('Завершение работы бота')
    if not TELEGRAM_TOKEN:
        logging.critical('Отсутствует токен TELEGRAM_TOKEN')
        sys.exit('Завершение работы бота')
    if not TELEGRAM_CHAT_ID:
        logging.critical('Отсутствует токен TELEGRAM_CHAT_ID')
        sys.exit('Завершение работы бота')


# def send_message(bot, message):
#     """Отправка сообщения пользователю."""
#     ...


def get_api_answer(timestamp):
    """Получение ответа от api яндекса."""
    payload = {'from_date': timestamp}
    try:
        logging.info('Попытка получения ответа от api')
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
        if response.status_code != HTTPStatus.OK:
            raise ConnectionError('ENDPOINT не доступен')
        return response.json()
    except:
        logging.critical('Не удалось получить ответ от api')
        raise ConnectionError('Не удалось получить ответ от api')


def check_response(response):
    """Проверка данных api на наличие ключевых составляющих."""
    logging.info('Проверка данных началась')
    if not isinstance(response, dict):
        raise TypeError('Ответ от api приходит не в типе данных dict')
    homeworks = response.get('homeworks')
    current_date = response.get('current_date')
    if not isinstance(homeworks, list):
        raise TypeError('homeworks приходит не в типе данных list')
    if not homeworks:
        raise KeyError('В ответе от api нет ключа homeworks')
    if not current_date:
        raise KeyError('В ответе от api нет ключа homeworks')
    return homeworks


def parse_status(homework):
    """Получения статуса работы"""
    last_homework = homework[0]
    homework_name = last_homework.get('homework_name')
    status = last_homework.get('status')
    if not homework_name:
        raise KeyError('В полученных данных нет ключа homework_name')
    if not status:
        raise KeyError('В полученных данных нет ключа status')
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Проверяем наличие всех токенов
    check_tokens()
    # Экземпляр класса Bot
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # Временная метка в unix формате
    timestamp = 0
    # Получаем ответ от api через функцию get_api_answer
    response = get_api_answer(timestamp)
    # Получаем корректные данные после проверки функцией check_response
    homework = check_response(response)
    parsed_homework = parse_status(homework)
    pprint(parsed_homework)


#     while True:
#         try:

#             ...

#         except Exception as error:
#             message = f'Сбой в работе программы: {error}'
#             ...
#         ...


if __name__ == '__main__':
    main()
