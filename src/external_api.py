import json
import os
import pathlib as p
import time
from typing import Any, Dict, Optional, Sequence

import requests
from dotenv import load_dotenv


def get_exchange_rates(
    base: str = "RUB", currencies: Sequence[str] = ("USD", "EUR", "CNY"), timeout: float = 20.0, max_retries: int = 2
) -> Optional[list[Dict[str, Any]]]:
    """Принимает коды валют: базовую (тип: str, пример: "RUB"), в которой рассчитывается стоимость; список валют валют,
    стоимость которых нужно рассчитать (тип: Sequence[str], пример: ('USD', 'EUR', 'CNY').
    Возвращает список словарей с курсами.
    Формат результата:
    [{'currency': 'USD', 'exchange_to': 'RUB', 'exchange_rate': 90.25},
     {'currency': 'EUR', 'exchange_to': 'RUB', 'exchange_rate': 98.50}]"""
    # Валидация параметров
    if not all(len(c) == 3 and c.isalpha() for c in [base, *currencies]):
        print("Ошибка: Неверный формат валюты. Используйте 3 буквенных символа (USD, RUB и т.д.)")
        return None

    if len(currencies) == 0:
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
            print("Ошибка: API_KEY_FOR_APILAYER не найден в .env")
            return None
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {str(e)}")
        return None
    # Формирование запроса
    url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={currencies_str.upper()}&base={base.upper()}"

    # Попытки запроса
    for attempt in range(max_retries + 1):
        try:
            response = requests.request("GET", url, headers=headers, timeout=timeout)

            # Проверка HTTP статуса
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                if response.status_code == 429:
                    error_msg += " (Превышен лимит запросов)"
                elif response.status_code == 401:
                    error_msg += " (Неверный API-ключ)"
                raise requests.exceptions.HTTPError(error_msg)

            # Парсинг JSON
            else:
                exchange_rate = response.json()

                # Валидация курсов
                # missing_currencies = [c for c in currencies if c not in exchange_rate['rates']]
                # if missing_currencies:
                #     raise ValueError(f"Отсутствуют курсы для: {', '.join(missing_currencies)}")
                #     continue
                # Формирование результата
                final_exch_rate = []
                for currency in currencies:
                    exchange_rate_reversed = {
                        "currency": currency.upper(),
                        "exchange_to": base.upper(),
                        "exchange_rate": round((1 / exchange_rate["rates"][currency.upper()]), 2),
                    }
                    final_exch_rate.append(exchange_rate_reversed)
                return final_exch_rate

        except requests.exceptions.RequestException as e:
            print(f"Попытка {attempt + 1} не удалась: {str(e)}")
            if attempt == max_retries:
                print("Превышено максимальное количество попыток")
                return None

            time.sleep(2**attempt)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Ошибка обработки данных: {str(e)}")
            return None

    raise RuntimeError("Непредвиденная ошибка: превышены все попытки запроса")


# data = get_exchange_rates("rub", ["usd", "eur", "JPY", "CNY"])
# if data:
#     for i in data:
#         print(i)
# else:
#     print("Ошибка загрузки данных")


# >>>{'currency': 'USD', 'exchange_to': 'CNY', 'exchange_rate': 7.25}
#    {'currency': 'EUR', 'exchange_to': 'CNY', 'exchange_rate': 7.85}
#    {'currency': 'JPY', 'exchange_to': 'CNY', 'exchange_rate': 0.05}
