import src.data_reader as data_reader
# import pandas as pd
import json
import pytz
from datetime import datetime, UTC
from tzlocal import get_localzone
from typing import List, Dict, Any

data = data_reader.xlsx_reader("data/operations.xlsx")

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


time_string = get_current_time()


def get_greeting(time_string: str) -> str:
    """Возвращает приветствие в зависимости от времени."""
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


print(get_current_time())
print(get_greeting(time_string))


def process_cards(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Обрабатывает данные по картам."""
    cards = {}
    amount = None
    for transaction in transactions:
        card = transaction.get("Номер карты", "")
        if card == 'nan' or not card:
            continue

        last_digits = card[-4:] if len(str(card)) >= 4 else card
        if transaction.get("Сумма операции", 0) < 0:
            amount = abs(transaction.get("Сумма операции", 0))
        else:
            0

        if last_digits not in cards:
            cards[last_digits] = {
                "last_digits": last_digits,
                "total_spent": 0.0,
                "cashback": 0.0
            }

        cards[last_digits]["total_spent"] += amount
        cashback = transaction.get("Бонусы (включая кэшбэк)", 0)
        if isinstance(cashback, (int, float)):
            cards[last_digits]["cashback"] += cashback

    return list(cards.values())


print(process_cards(data))


def get_top_transactions(transactions: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    """Возвращает топ-N транзакций по сумме."""
    valid_transactions = [
        t for t in transactions
        if isinstance(t.get("Сумма операции"), (int, float)) and t.get("Сумма операции", 0) < 0
    ]

    sorted_transactions = sorted(valid_transactions, key=lambda x: abs(x["Сумма операции"]), reverse=True)[:n]

    top_transactions = []
    for t in sorted_transactions:
        top_transactions.append({
            "date": t.get("Дата операции", "").split()[0],
            "amount": abs(t.get("Сумма операции", 0)),
            "category": t.get("Категория", ""),
            "description": t.get("Описание", "")
        })

def get_currency_rates() -> List[Dict[str, Any]]:
    """Возвращает курсы валют (заглушка)."""
    return [
        {"currency": "USD", "rate": 73.21},
        {"currency": "EUR", "rate": 87.08}
    ]


    return top_transactions
for transaction in get_top_transactions(data, 10):
    print(transaction)



