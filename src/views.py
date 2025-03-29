import json
import logging
import os
import pathlib as p
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from tzlocal import get_localzone

import src.data_reader as data_reader
import src.external_api as external_api

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


def get_current_time() -> str:
    """Возвращает текущее время в формате 'YYYY-MM-DD HH:MM:SS' с учётом временной зоны системы.
    Пример: '2023-12-25 15:30:45'"""

    try:
        # Получаем временную зону системы (например, 'Asia/Yekaterinburg')
        local_tz = get_localzone()
        current_time = datetime.now(local_tz)
        time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(f"Успешно получено локальное время: {time}")
    except Exception as e:
        # Если что-то пошло не так, возвращаем UTC время
        logger.warning(f"Ошибка определения временной зоны: {e}. Используется UTC.")
        print(f"Ошибка определения зоны: {e}. Используется UTC.")
        current_time = datetime.now(UTC)
        time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return time


def get_greeting() -> str:
    """Возвращает приветствие в зависимости от времени."""

    time_string = get_current_time()
    date = datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
    hour = date.hour
    if 5 <= hour < 12:
        greeting = "Доброе утро"
    elif 12 <= hour < 17:
        greeting = "Добрый день"
    elif 17 <= hour < 23:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"
    logger.debug(f"Определено приветствие: {greeting} (время: {hour}:00)")
    return greeting


def process_cards(transactions: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Обрабатывает данные по картам."""

    logger.info(f"Начало обработки {len(list(transactions))} транзакций")
    cards: Dict[str, Dict[str, Any]] = {}
    for transaction in transactions:
        card = transaction.get("Номер карты", "")
        if card == "nan" or not card:
            logger.debug("Транзакция пропущена (нет номера карты)")
            continue

        last_digits = card[-4:] if len(str(card)) >= 4 else card
        if transaction.get("Сумма операции", 0) < 0:
            amount = abs(transaction.get("Сумма операции", 0))
        else:
            amount = 0

        if last_digits not in cards:
            cards[last_digits] = {"last_digits": last_digits, "total_spent": 0.0, "cashback": 0.0}

        cards[last_digits]["total_spent"] += amount
        cashback = transaction.get("Бонусы (включая кэшбэк)", 0)
        if isinstance(cashback, (int, float)):
            cards[last_digits]["cashback"] += cashback
        logger.debug(f"Транзакция: карта {last_digits}, сумма: {amount}, кэшбэк: {cashback}")

    logger.info(f"Обработано {len(cards)} карт")
    return list(cards.values())


def get_top_transactions(transactions: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    """Возвращает топ-N транзакций по сумме."""

    logger.info(f"Поиск топ-{n} транзакций из {len(transactions)}")
    valid_transactions = [
        t for t in transactions if isinstance(t.get("Сумма операции"), (int, float)) and t.get("Сумма операции", 0) < 0
    ]
    logger.debug(f"Найдено {len(valid_transactions)} валидных транзакций")

    sorted_transactions = sorted(valid_transactions, key=lambda x: abs(x["Сумма операции"]), reverse=True)[:n]

    top_transactions = []
    for t in sorted_transactions:
        date_str = t.get("Дата операции", "")
        date = date_str.split()[0] if date_str else ""
        transaction_data = {
            "date": date,
            "amount": abs(t.get("Сумма операции", 0)),
            "category": t.get("Категория", ""),
            "description": t.get("Описание", ""),
        }
        top_transactions.append(transaction_data)
        logger.debug(f"Добавлена транзакция: {transaction_data}")

    logger.info(f"Сформировано {len(top_transactions)} топ-транзакций")
    return top_transactions


def get_currency_rates(currencies: Sequence[str] = ("USD", "EUR", "CNY")) -> Optional[List[Dict[str, Any]] | Any]:
    """Возвращает актуальные курсы валют по отношению к рублю"""

    logger.info(f"Запрос курсов валют: {currencies}")
    try:
        exchange_rates = external_api.get_exchange_rates("RUB", currencies)
        if not exchange_rates:
            logger.warning("Не удалось получить курсы валют")
            return None

        result = []
        for currency in exchange_rates:
            try:
                rate_data = {currency["currency"]: currency["exchange_rate"]}
                result.append(rate_data)
                logger.debug(f"Добавлен курс: {rate_data}")

            except Exception as e:
                logger.warning(f"Ошибка обработки курса валюты: {e}")

        logger.info(f"Получено {len(result)} курсов валют")
        return result

    except Exception as e:
        logger.error(f"Ошибка в get_currency_rates: {e}")
        return None


def get_stock_prices(
    resource: str = "finnhub", tickers: Sequence[str] = ("MSFT", "AAPL", "TSLA")
) -> List[Dict[str, Any]]:
    """Возвращает цены акций из S&P500. Принимает на вход название ресурса,
    с которого производится загрузка данных по фондовому рынку."""
    logger.info(f"Запрос цен акций ({resource}): {tickers}")

    try:
        if resource != "finnhub":
            logger.warning(f"Неподдерживаемый ресурс: {resource}")
            return []

        data = external_api.get_stock_rates_finnhub(tickers)
        if data is None:
            logger.warning("Не удалось получить данные об акциях")
            return []

        stock_prices = []
        for ticker in data:
            try:
                ticker_price = {ticker["ticker"]: ticker.get("current_price")}
                stock_prices.append(ticker_price)
                logger.debug(f"Добавлена акция: {ticker_price}")
            except KeyError:
                logger.warning("Пропущена акция с неполными данными")
                continue

        logger.info(f"Получено {len(stock_prices)} цен акций")
        return stock_prices

    except Exception as e:
        logger.error(f"Ошибка в get_stock_prices: {e}")
        return []


def main_page() -> str:
    """Главная функция, обрабатывающая данные и возвращающая JSON-ответ"""
    # Парсим входные данные
    logger.info("Запуск main_page")

    try:
        logger.debug("Чтение данных из XLSX")
        data = data_reader.xlsx_reader("data/operations.xlsx")

        response = {
            "greeting": get_greeting(),
            "cards": process_cards(data),
            "top_transactions": get_top_transactions(data, 5),
            "currency_rates": get_currency_rates(),
            "stock_prices": get_stock_prices(),
        }

        logger.debug("Формирование JSON-ответа")
        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        logger.info("Успешное завершение main_page")
        return json_response
    except Exception as e:
        logger.critical(f"Критическая ошибка в main_page: {e}")
        return json.dumps({"error": "Internal Server Error"}, ensure_ascii=False, indent=4)


print(main_page())
