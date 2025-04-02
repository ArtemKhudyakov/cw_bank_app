import json
import logging
import os
import pathlib as p
import time
from typing import Any, Dict, Optional, Sequence

import requests
from dotenv import load_dotenv

# Получаем имя модуля
module_name = p.Path(__file__).stem

# Путь к корневой папке
current_file_path = p.Path(__file__).resolve()
project_root_path = current_file_path.parent.parent

# Путь к папке "logs"
logs_dir = project_root_path / "logs"

# Создаем папку logs если её нет
os.makedirs(logs_dir, exist_ok=True)

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f"{project_root_path}/logs/{module_name}.log", encoding="utf-8", mode="w")
file_formater = logging.Formatter("%(asctime)s - %(name)s -%(funcName)s - %(lineno)d - %(levelname)s -" " %(message)s")
file_handler.setFormatter(file_formater)
logger.addHandler(file_handler)


def get_exchange_rates(
    base: str = "RUB", currencies: Sequence[str] = ("USD", "EUR", "CNY"), timeout: float = 5.0, max_retries: int = 2
) -> Optional[list[Dict[str, Any]]]:
    """Принимает коды валют: базовую (тип: str, пример: "RUB"), в которой рассчитывается стоимость; список валют валют,
    стоимость которых нужно рассчитать (тип: Sequence[str], пример: ('USD', 'EUR', 'CNY').
    Возвращает список словарей с курсами.
    Формат результата:
    [{'currency': 'USD', 'exchange_to': 'RUB', 'exchange_rate': 90.25},
     {'currency': 'EUR', 'exchange_to': 'RUB', 'exchange_rate': 98.50}]"""
    logger.debug(f"Начало get_exchange_rates. Базовая валюта: {base}, целевые: {currencies}")
    # Валидация параметров
    if not all(len(c) == 3 and c.isalpha() for c in [base, *currencies]):
        error_msg = "Неверный формат валюты. Используйте 3 буквенных символа (USD, RUB и т.д.)"
        logger.error(error_msg)
        print("Ошибка: Неверный формат валюты. Используйте 3 буквенных символа (USD, RUB и т.д.)")
        return None

    if len(currencies) == 0:
        error_msg = "Список валют не может быть пустым"
        logger.error(error_msg)
        print("Ошибка: Список валют не может быть пустым")
        return None
    # Загрузка API-ключа
    try:
        current_file_path = p.Path(__file__).resolve()
        project_root_path = current_file_path.parent.parent
        load_dotenv(dotenv_path=f"{project_root_path}/.env")
        API_KEY = os.getenv("API_KEY_FOR_APILAYER")
        currencies_str = ",".join(currencies)
        headers = {"apikey": API_KEY}

        if not API_KEY:
            error_msg = "API_KEY_FOR_APILAYER не найден в .env"
            logger.error(error_msg)
            print("Ошибка: API_KEY_FOR_APILAYER не найден в .env")
            return None
        logger.debug("Конфигурация успешно загружена")
    except Exception as e:
        error_msg = f"Ошибка загрузки конфигурации: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"Ошибка загрузки конфигурации: {str(e)}")
        return None
    # Формирование запроса
    url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={currencies_str.upper()}&base={base.upper()}"
    logger.debug(f"Формирование запроса к URL: {url}")
    # Попытки запроса
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Попытка {attempt + 1} из {max_retries + 1}")
            response = requests.request("GET", url, headers=headers, timeout=timeout)
            logger.debug(f"Получен ответ: статус {response.status_code}")

            # Проверка HTTP статуса
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                if response.status_code == 429:
                    error_msg += " (Превышен лимит запросов)"
                elif response.status_code == 401:
                    error_msg += " (Неверный API-ключ)"
                logger.error(error_msg)
                raise requests.exceptions.HTTPError(error_msg)

            # Парсинг JSON
            else:
                exchange_rate = response.json()
                logger.debug("Успешно распарсен JSON ответ")
                final_exch_rate = []
                for currency in currencies:
                    rate = round((1 / exchange_rate["rates"][currency.upper()]), 2)
                    exchange_rate_reversed = {
                        "currency": currency.upper(),
                        "exchange_to": base.upper(),
                        "exchange_rate": rate,
                    }
                    final_exch_rate.append(exchange_rate_reversed)
                    logger.debug(f"Добавлен курс: {currency.upper()} -> {base.upper()} = {rate}")
                logger.info("Успешно получены курсы валют")
                return final_exch_rate

        except requests.exceptions.RequestException as e:
            logger.warning(f"Попытка {attempt + 1} не удалась: {str(e)}", exc_info=True)
            print(f"Попытка {attempt + 1} не удалась: {str(e)}")
            if attempt == max_retries:
                logger.error("Превышено максимальное количество попыток")
                print("Превышено максимальное количество попыток")
                return None

            time.sleep(2**attempt)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка обработки данных: {str(e)}", exc_info=True)
            print(f"Ошибка обработки данных: {str(e)}")
            return None

    logger.critical("Непредвиденная ошибка: превышены все попытки запроса")
    raise RuntimeError("Непредвиденная ошибка: превышены все попытки запроса")


def get_stock_rates_finnhub(
    stock: Sequence[str] = ("MSFT", "AAPL", "TSLA"), timeout: float = 5.0, max_retries: int = 2
) -> Optional[list[Dict[str, Any]]]:
    """Принимает коды валют: базовую (тип: str, пример: "RUB"), в которой рассчитывается стоимость;
    список валют валют, стоимость которых нужно рассчитать (тип: Sequence[str], пример: ('USD', 'EUR', 'CNY').
    Возвращает список словарей с курсами.
    Формат результата:
    [{'currency': 'USD', 'exchange_to': 'RUB', 'exchange_rate': 90.25},
     {'currency': 'EUR', 'exchange_to': 'RUB', 'exchange_rate': 98.50}]"""

    logger.debug(f"Начало get_stock_rates_finnhub. Тикеры: {stock}")
    try:
        current_file_path = p.Path(__file__).resolve()
        project_root_path = current_file_path.parent.parent
        load_dotenv(dotenv_path=f"{project_root_path}/.env")
        API_KEY = os.getenv("FINHUB_API_KEY")

        if not API_KEY:
            error_msg = "FINHUB_API_KEY не найден в .env"
            logger.error(error_msg)
            print("Ошибка: FINHUB_API_KEY не найден в .env")
            return None
        logger.debug("Конфигурация успешно загружена")
    except Exception as e:
        error_msg = f"Ошибка загрузки конфигурации: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"Ошибка загрузки конфигурации: {str(e)}")
        return None

    # Формирование запроса
    stock_data = []

    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Попытка {attempt + 1} из {max_retries + 1}")
            for ticker in stock:
                url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={API_KEY}"
                logger.debug(f"Запрос данных для {ticker} по URL: {url}")
                response = requests.get(url, timeout=timeout)
                logger.debug(f"Получен ответ: статус {response.status_code}")

                data = response.json()
                logger.debug(f"Данные ответа: {data}")

                ticker_info = {
                    "ticker": f"{ticker}",
                    "current_price": data["c"],
                    "change": data["d"],
                    "percent_change": data["dp"],
                    "high": data["h"],
                    "low": data["l"],
                    "open": data["o"],
                    "previous_close": data["pc"],
                }

                stock_data.append(ticker_info)
                logger.debug(f"Добавлены данные по {ticker}")

                # Проверка HTTP статуса
                if response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}"
                    if response.status_code == 429:
                        error_msg += " (Превышен лимит запросов)"
                    elif response.status_code == 401:
                        error_msg += " (Неверный API-ключ)"
                    logger.error(error_msg)
                    raise requests.exceptions.HTTPError(error_msg)
            logger.info(f"Успешно получены данные по {len(stock)} акциям")
            return stock_data

        except requests.exceptions.RequestException as e:
            logger.warning(f"Попытка {attempt + 1} не удалась: {str(e)}", exc_info=True)
            print(f"Попытка {attempt + 1} не удалась: {str(e)}")
            if attempt == max_retries:
                print("Превышено максимальное количество попыток")
                logger.error("Превышено максимальное количество попыток")
                return None

            time.sleep(2**attempt)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка обработки данных: {str(e)}", exc_info=True)
            print(f"Ошибка обработки данных: {str(e)}")
            return None
    logger.critical("Непредвиденная ошибка: превышены все попытки запроса")
    return None


# Получение данных о котировках акций с сайта https://www.alphavantage.co
# def get_stock_rates_av(
#         stock: Sequence[str] = ('MSFT', 'AAPL', 'TSLA'), timeout: float = 20.0,
#         max_retries: int = 2
# ) -> Optional[list[Dict[str, Any]]]:
#     """Принимает коды валют: базовую (тип: str, пример: "RUB"), в которой рассчитывается стоимость; список валют
#     валют, стоимость которых нужно рассчитать (тип: Sequence[str], пример: ('USD', 'EUR', 'CNY').
#     Возвращает список словарей с курсами.
#     Формат результата:
#     [{'currency': 'USD', 'exchange_to': 'RUB', 'exchange_rate': 90.25},
#      {'currency': 'EUR', 'exchange_to': 'RUB', 'exchange_rate': 98.50}]"""
#     try:
#         current_file_path = p.Path(__file__).resolve()
#         project_root_path = current_file_path.parent.parent
#         load_dotenv(dotenv_path=f"{project_root_path}/.env")
#         API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
#
#         if not API_KEY:
#             print("Ошибка: ALPHAVANTAGE_API_KEY не найден в .env")
#             return None
#     except Exception as e:
#         print(f"Ошибка загрузки конфигурации: {str(e)}")
#         return None
#
#     # Формирование запроса
#     list_of_responses = []
#
#     for attempt in range(max_retries + 1):
#         try:
#             for ticker in stock:
#                 url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={API_KEY}"
#                 response = requests.get(url)
#                 list_of_responses.append(response.json())
#
#                 # Проверка HTTP статуса
#                 if response.status_code != 200:
#                     error_msg = f"HTTP {response.status_code}"
#                     if response.status_code == 429:
#                         error_msg += " (Превышен лимит запросов)"
#                     elif response.status_code == 401:
#                         error_msg += " (Неверный API-ключ)"
#                     raise requests.exceptions.HTTPError(error_msg)
#             return list_of_responses
#
#
#         except requests.exceptions.RequestException as e:
#             print(f"Попытка {attempt + 1} не удалась: {str(e)}")
#             if attempt == max_retries:
#                 print("Превышено максимальное количество попыток")
#                 return None
#
#             time.sleep(2 ** attempt)
#
#         except (json.JSONDecodeError, ValueError) as e:
#             print(f"Ошибка обработки данных: {str(e)}")
#             return None
#
#     raise RuntimeError("Непредвиденная ошибка: превышены все попытки запроса")
