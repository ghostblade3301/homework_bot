import os
import logging
import time
import requests
import telegram
import sys

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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def check_tokens():
    """Проверка наличия токенов."""
    if not PRACTICUM_TOKEN:
        logger.critical('Отсутствует токен PRACTICUM_TOKEN')
        sys.exit()
    elif not TELEGRAM_TOKEN:
        logger.critical('Отсутствует токен TELEGRAM_TOKEN')
        sys.exit()
    elif not TELEGRAM_CHAT_ID:
        logger.critical('Отсутствует токен TELEGRAM_CHAT_ID')
        sys.exit()


# def send_message(bot, message):
#     """Отправка сообщения в телеграм."""
#     pass


def get_api_answer(timestamp):
    """Получение ответа от api."""
    homework_statuses = requests.get(ENDPOINT,
                                     headers=HEADERS,
                                     params=timestamp,)
    return homework_statuses.json()


def check_response(response):
    """Проверка ответа."""
    # Проверим, что приходит dict
    if not isinstance(response, dict):
        raise TypeError('Несоответствие типу. На вход ожидался тип dict')
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks не найден')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('Несоответствие типу. На вход ожидался тип list')
    if not response.get('date_updated'):
        raise KeyError('Ключ date_updated не найден')


def parse_status(homework):
    """Проверка статуса работы."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неопределенный статус {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = {'from_date': int(time.time())}
    while True:
        try:
            homework_response = get_api_answer(timestamp)
            check_doc_homework = check_response(homework_response)
            if not check_doc_homework:
                logger.debug('Нет обновлений')
            homework = check_doc_homework[0]
            message = parse_status(homework)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            



if __name__ == '__main__':
    main()

