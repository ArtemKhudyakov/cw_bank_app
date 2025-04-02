from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from src.external_api import get_exchange_rates, get_stock_rates_finnhub


def test_successful_response() -> None:
    """Тест успешного получения курсов валют"""
    test_data = {"rates": {"USD": 0.011, "EUR": 0.010}, "base": "RUB"}

    with patch("requests.request") as mock_request:
        # Настраиваем mock-ответ
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = test_data

        # Мокаем переменные окружения
        with patch.dict("os.environ", {"API_KEY_FOR_APILAYER": "test_key"}):
            result = get_exchange_rates(currencies=["USD", "EUR"])

    assert result == [
        {"currency": "USD", "exchange_to": "RUB", "exchange_rate": 90.91},
        {"currency": "EUR", "exchange_to": "RUB", "exchange_rate": 100.0},
    ]


def test_invalid_currency() -> None:
    """Тест с неверным кодом валюты"""
    result = get_exchange_rates(base="RUB1")
    assert result is None


def test_api_error() -> None:
    """Тест ошибки API"""
    with patch("requests.request") as mock_request:
        mock_request.return_value.status_code = 401  # Неавторизован
        with patch.dict("os.environ", {"API_KEY_FOR_APILAYER": "test_key"}):
            result = get_exchange_rates()
    assert result is None


def test_empty_currencies() -> None:
    """Тест пустого списка валют"""
    result = get_exchange_rates(currencies=[])
    assert result is None


def test_missing_api_key() -> None:
    """Тест отсутствия API-ключа"""
    with patch.dict("os.environ", {}, clear=True):
        with patch("requests.request"):
            # Убедитесь, что функция не пытается делать реальные запросы
            result = get_exchange_rates()
    assert result is None


def test_successful_response_fh(stock_test_response: dict[str, int]) -> None:
    """Тест успешного получения данных об акциях"""

    with patch("requests.get") as mock_get:
        # Настраиваем mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = stock_test_response

        # Мокаем переменные окружения
        with patch.dict("os.environ", {"FINHUB_API_KEY": "test_key"}):
            result = get_stock_rates_finnhub(stock=["AAPL"])

    assert result == [
        {
            "ticker": "AAPL",
            "current_price": 150.0,
            "change": 1.5,
            "percent_change": 1.01,
            "high": 152.0,
            "low": 149.0,
            "open": 151.0,
            "previous_close": 148.5,
        }
    ]


@pytest.mark.parametrize(
    "stock_test_response, expected_result",
    [
        # Базовый случай для AAPL
        (
            {
                "c": 150.0,  # current price
                "d": 1.5,  # change
                "dp": 1.01,  # percent change
                "h": 152.0,  # high
                "l": 149.0,  # low
                "o": 151.0,  # open
                "pc": 148.5,  # previous close
            },
            [
                {
                    "ticker": "AAPL",
                    "current_price": 150.0,
                    "change": 1.5,
                    "percent_change": 1.01,
                    "high": 152.0,
                    "low": 149.0,
                    "open": 151.0,
                    "previous_close": 148.5,
                }
            ],
        ),
        # Тест для другой акции (MSFT)
        (
            {"c": 250.0, "d": -2.5, "dp": -0.99, "h": 255.0, "l": 248.0, "o": 252.0, "pc": 252.5},
            [
                {
                    "ticker": "MSFT",
                    "current_price": 250.0,
                    "change": -2.5,
                    "percent_change": -0.99,
                    "high": 255.0,
                    "low": 248.0,
                    "open": 252.0,
                    "previous_close": 252.5,
                }
            ],
        ),
        # Тест с нулевыми значениями
        (
            {"c": 0.0, "d": 0.0, "dp": 0.0, "h": 0.0, "l": 0.0, "o": 0.0, "pc": 0.0},
            [
                {
                    "ticker": "TEST",
                    "current_price": 0.0,
                    "change": 0.0,
                    "percent_change": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "open": 0.0,
                    "previous_close": 0.0,
                }
            ],
        ),
    ],
    ids=["apple_stock_data", "microsoft_stock_data", "zero_values_data"],
)
def test_successful_response_fh_parametrized(
    stock_test_response: List[Dict[str, float]], expected_result: List[Dict[str, Any]]
) -> None:
    """Тест успешного получения данных об акциях"""
    with patch("requests.get") as mock_get:
        # Настраиваем mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = stock_test_response

        # Мокаем переменные окружения
        with patch.dict("os.environ", {"FINHUB_API_KEY": "test_key"}):
            # Получаем тикер из ожидаемого результата
            ticker = expected_result[0]["ticker"]
            result = get_stock_rates_finnhub(stock=[ticker])

    assert result == expected_result


def test_missing_api_key_fh() -> None:
    """Тест отсутствия API-ключа"""
    # 1. Полностью очищаем переменные окружения
    with patch.dict("os.environ", {}, clear=True):
        # 2. Мокаем os.getenv чтобы гарантированно возвращал None
        with patch("os.getenv", return_value=None) as mock_getenv:
            # 3. Мокаем print для проверки сообщения
            with patch("builtins.print") as mock_print:
                result = get_stock_rates_finnhub()

    # Проверки
    assert result is None
    mock_getenv.assert_called_with("FINHUB_API_KEY")
    mock_print.assert_called_with("Ошибка: FINHUB_API_KEY не найден в .env")


def test_http_error() -> None:
    """Тест ошибки HTTP запроса"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 401  # Unauthorized
        with patch.dict("os.environ", {"FINHUB_API_KEY": "test_key"}):
            result = get_stock_rates_finnhub()
    assert result is None


def test_multiple_stocks(stock_test_response: List[Dict[str, float]]) -> None:
    """Тест обработки нескольких акций"""

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = stock_test_response

        with patch.dict("os.environ", {"FINHUB_API_KEY": "test_key"}):
            result = get_stock_rates_finnhub(stock=["AAPL", "MSFT"])
    assert result is not None
    assert len(result) == 2
    assert result[0]["ticker"] == "AAPL"
    assert result[1]["ticker"] == "MSFT"


def test_invalid_json_response() -> None:
    """Тест невалидного JSON ответа"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")

        with patch.dict("os.environ", {"FINHUB_API_KEY": "test_key"}):
            result = get_stock_rates_finnhub()

    assert result is None
