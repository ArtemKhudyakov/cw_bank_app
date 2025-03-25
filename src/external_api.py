import os
import json
from typing import Any
import pathlib as p
import requests
from dotenv import load_dotenv


def get_exchange_rates(base: str = 'RUB', currencies: list[str]|tuple[str]=('USD', 'EUR', 'CNY')):
    current_file_path = p.Path(__file__).resolve()
    project_root_path = current_file_path.parent.parent
    load_dotenv(dotenv_path=f'{project_root_path}/.env')
    API_KEY = os.getenv('API_KEY_FOR_APILAYER')
    currencies_str = ','.join(currencies)
    url = f'https://api.apilayer.com/exchangerates_data/latest?symbols={currencies_str}&base={base}'
    headers = {"apikey": API_KEY}
    response = requests.request("GET", url, headers=headers)
    exchange_rate=(json.loads(response.text))
    print(exchange_rate)
    final_exch_rate = []
    for currency in currencies:
        exchange_rate_reversed = {"currency": currency, "exchange_to": base, "exchange_rate": round((1/exchange_rate['rates'][currency]), 2)}
        final_exch_rate.append(exchange_rate_reversed)

    return final_exch_rate

for i in get_exchange_rates("CNY", ['USD', 'EUR', 'JPY']):
    print(i)

# >>>{'currency': 'USD', 'exchange_to': 'CNY', 'exchange_rate': 7.25}
#    {'currency': 'EUR', 'exchange_to': 'CNY', 'exchange_rate': 7.85}
#    {'currency': 'JPY', 'exchange_to': 'CNY', 'exchange_rate': 0.05}
