import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

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


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Сообщение не отправлено причина: {error}')


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
    except Exception as error:
        logging.critical('Не удалось получить ответ от api')
        raise ConnectionError(f'Не удалось получить ответ от api: {error}')


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
        raise KeyError('В ответе от api нет ключа current_date')
    return homeworks[0]


def parse_status(homework):
    """Получения статуса работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if not homework_name:
        raise KeyError('В полученных данных нет ключа homework_name')
    if not status:
        raise KeyError('В полученных данных нет ключа status')
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неопределенный статус {status}')
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Проверяем наличие всех токенов
    check_tokens()
    # Экземпляр класса Bot
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # Временная метка в unix формате
    timestamp = int(time.time())
    hwork_status = None
    while True:
        try:
            # Получаем ответ от api через функцию get_api_answer
            response = get_api_answer(timestamp)
            # Получаем корректные данные после проверки функцией check_response
            homework = check_response(response)
            parsed_homework = parse_status(homework)
            if homework:
                hwork_status_old = hwork_status
                hwork_status = parsed_homework
                if (hwork_status_old != hwork_status):
                    send_message(bot, hwork_status)
                else:
                    send_message(bot, 'Статус не изменился')
            else:
                hwork_status_old = None
                hwork_status = None
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, [%(levelname)s] %(message)s',
        stream=sys.stdout,
    )
    main()
