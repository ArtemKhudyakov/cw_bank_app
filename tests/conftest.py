from typing import Any, Dict, Generator, List
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def basic_transactions() -> List[Dict[str, Any]]:
    """Фикстура возвращает базовый набор транзакций"""
    return [
        {"Номер карты": "1234567812345678", "Сумма операции": -1000, "Бонусы (включая кэшбэк)": 50},
        {"Номер карты": "8765432187654321", "Сумма операции": -500, "Бонусы (включая кэшбэк)": 25},
        {"Номер карты": "1234567812345678", "Сумма операции": -2000, "Бонусы (включая кэшбэк)": 100},
    ]


@pytest.fixture
def invalid_cards() -> List[Dict[str, Any]]:
    return [
        {"Номер карты": "", "Сумма операции": -100},  # Пустой номер
        {"Номер карты": "nan", "Сумма операции": -200},  # Строка 'nan'
        {"Номер карты": None, "Сумма операции": -300},  # None значение
        {"Номер карты": "1234", "Сумма операции": -400},  # Валидная карта
    ]


@pytest.fixture
def mock_api() -> Generator[Mock]:
    with patch("src.utils.external_api.get_exchange_rates") as mock:
        yield mock


@pytest.fixture
def mock_finnhub() -> Generator[Mock]:
    """Фикстура для мокирования external_api.get_stock_rates_finnhub.
    Возвращает: Mock: Мок-объект для подмены реального API Finnhub"""
    with patch("src.utils.external_api.get_stock_rates_finnhub") as mock:
        yield mock


@pytest.fixture
def mock_dependencies() -> Generator[Dict[str, Mock]]:
    """Фикстура для мокирования всех зависимостей"""
    with (
        patch("src.utils.data_reader.xlsx_reader") as mock_reader,
        patch("src.utils.get_greeting") as mock_greeting,
        patch("src.utils.process_cards") as mock_cards,
        patch("src.utils.get_top_transactions") as mock_top,
        patch("src.utils.get_currency_rates") as mock_rates,
        patch("src.utils.get_stock_prices") as mock_stocks,
    ):
        # Настраиваем моки
        mock_reader.return_value = [{"test": "data"}]
        mock_greeting.return_value = "Добрый день"
        mock_cards.return_value = [{"card": "test"}]
        mock_top.return_value = [{"transaction": "test"}]
        mock_rates.return_value = [{"USD": 90.5}]
        mock_stocks.return_value = [{"AAPL": 150.0}]

        yield {
            "mock_reader": mock_reader,
            "mock_greeting": mock_greeting,
            "mock_cards": mock_cards,
            "mock_top": mock_top,
            "mock_rates": mock_rates,
            "mock_stocks": mock_stocks,
        }


@pytest.fixture
def stock_test_response() -> Dict[str, float]:
    return {
        "c": 150.0,  # current_price
        "d": 1.5,  # change
        "dp": 1.01,  # percent_change
        "h": 152.0,  # high
        "l": 149.0,  # low
        "o": 151.0,  # open
        "pc": 148.5,  # previous_close
    }
