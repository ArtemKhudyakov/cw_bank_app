import json
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Hashable
import src.external_api as external_api

from tzlocal import get_localzone

import src.data_reader as data_reader


# data_dict = [
#     {
#         "Дата операции": "03.01.2018 15:03:35",
#         "Дата платежа": "04.01.2018",
#         "Номер карты": "*7197",
#         "Статус": "OK",
#         "Сумма операции": -73.06,
#         "Валюта операции": "RUB",
#         "Сумма платежа": -73.06,
#         "Валюта платежа": "RUB",
#         "Кэшбэк": 'nan',
#         "Категория": "Супермаркеты",
#         "MCC": 5499.0,
#         "Описание": "Magazin 25",
#         "Бонусы (включая кэшбэк)": 1,
#         "Округление на инвесткопилку": 0,
#         "Сумма операции с округлением": 73.06,
#     },
#     {
#         "Дата операции": "03.01.2018 14:55:21",
#         "Дата платежа": "05.01.2018",
#         "Номер карты": "*7197",
#         "Статус": "OK",
#         "Сумма операции": -21.0,
#         "Валюта операции": "RUB",
#         "Сумма платежа": -21.0,
#         "Валюта платежа": "RUB",
#         "Кэшбэк": 'nan',
#         "Категория": "Красота",
#         "MCC": 5977.0,
#         "Описание": "OOO Balid",
#         "Бонусы (включая кэшбэк)": 0,
#         "Округление на инвесткопилку": 0,
#         "Сумма операции с округлением": 21.0,
#     },
#     {
#         "Дата операции": "01.01.2018 20:27:51",
#         "Дата платежа": "04.01.2018",
#         "Номер карты": "*7197",
#         "Статус": "OK",
#         "Сумма операции": -316.0,
#         "Валюта операции": "RUB",
#         "Сумма платежа": -316.0,
#         "Валюта платежа": "RUB",
#         "Кэшбэк": 'nan',
#         "Категория": "Красота",
#         "MCC": 5977.0,
#         "Описание": "OOO Balid",
#         "Бонусы (включая кэшбэк)": 6,
#         "Округление на инвесткопилку": 0,
#         "Сумма операции с округлением": 316.0,
#     },
#     {
#         "Дата операции": "01.01.2018 12:49:53",
#         "Дата платежа": "01.01.2018",
#         "Номер карты": 'nan',
#         "Статус": "OK",
#         "Сумма операции": -3000.0,
#         "Валюта операции": "RUB",
#         "Сумма платежа": -3000.0,
#         "Валюта платежа": "RUB",
#         "Кэшбэк": 'nan',
#         "Категория": "Переводы",
#         "MCC": 'nan',
#         "Описание": "Линзомат ТЦ Юность",
#         "Бонусы (включая кэшбэк)": 0,
#         "Округление на инвесткопилку": 0,
#         "Сумма операции с округлением": 3000.0,
#     },
# ]


def get_current_time() -> str:
    """
    Возвращает текущее время в формате 'YYYY-MM-DD HH:MM:SS' с учётом временной зоны системы.
    Пример: '2023-12-25 15:30:45'
    """
    try:
        # Получаем временную зону системы (например, 'Asia/Yekaterinburg')
        local_tz = get_localzone()
        current_time = datetime.now(local_tz)
        time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        # Если что-то пошло не так, возвращаем UTC время
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
        return "Доброе утро"
    elif 12 <= hour < 17:
        return "Добрый день"
    elif 17 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def process_cards(transactions: List[Dict[Hashable, Any]]) -> List[Dict[Hashable, Any]]:
    """Обрабатывает данные по картам."""
    cards = {}
    for transaction in transactions:
        card = transaction.get("Номер карты", "")
        if card == "nan" or not card:
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

    return list(cards.values())


def get_top_transactions(transactions: List[Dict[Hashable, Any]], n: int = 5) -> List[Dict[Hashable, Any]]:
    """Возвращает топ-N транзакций по сумме."""
    valid_transactions = [
        t for t in transactions if isinstance(t.get("Сумма операции"), (int, float)) and t.get("Сумма операции", 0) < 0
    ]

    sorted_transactions = sorted(valid_transactions, key=lambda x: abs(x["Сумма операции"]), reverse=True)[:n]

    top_transactions = []
    for t in sorted_transactions:
        date_str = t.get("Дата операции", "")
        date = date_str.split()[0] if date_str else ""
        top_transactions.append(
            {
                "date": date,
                "amount": abs(t.get("Сумма операции", 0)),
                "category": t.get("Категория", ""),
                "description": t.get("Описание", ""),
            }
        )
    return top_transactions


def get_currency_rates(currencies = ('USD', 'EUR', 'CNY')) -> Optional[List[Dict[str, Any]] | Any]:
    """Возвращает актуальные курсы валют по отношению к рублю"""
    exchange_rates = external_api.get_exchange_rates("rub", currencies)
    result = []
    if exchange_rates:
        for currency in exchange_rates:
            exchange_rate_to_rub = {currency['currency']: currency['exchange_rate']}
            result.append(exchange_rate_to_rub)
        return result
    else:
        return None


def get_stock_prices(resource = "finnhub", tickers = ('MSFT', 'AAPL', 'TSLA')) -> List[Dict[str, Any]]:
    """Возвращает цены акций из S&P500. Принимает на вход название ресурса,
    с которого производится загрузка данных по фондовому рынку."""
    if resource == "finnhub":
        data = external_api.get_stock_rates_finnhub(tickers)
        stock_prices = []
        for ticker in data:
            try:
                ticker_price = {
                    ticker["ticker"]: ticker.get("current_price", None)
                }
                stock_prices.append(ticker_price)
            except KeyError:
                continue  # Пропускаем записи без тикера
        return stock_prices


def main_page():
    """Главная функция, обрабатывающая данные и возвращающая JSON-ответ"""
    # Парсим входные данные, если они в формате строки
    data = data_reader.xlsx_reader("data/operations.xlsx")
    greeting = get_greeting()
    cards = process_cards(data)
    top_transactions = get_top_transactions(data, 5)
    currency_rates = get_currency_rates()
    stock_prices = get_stock_prices()

    response = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }

    return json.dumps(response, ensure_ascii=False, indent=4)


print(main_page())
