import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.views import (
    get_currency_rates,
    get_current_time,
    get_greeting,
    get_stock_prices,
    get_top_transactions,
    main_page,
    process_cards
)


def test_get_current_time_format()->None:
    """Тест формата возвращаемого времени"""
    with patch("src.views.datetime") as mock_datetime:
        test_time = datetime(2023, 12, 25, 15, 30, 45)
        mock_datetime.now.return_value = test_time
        result = get_current_time()
        assert result == "2023-12-25 15:30:45"


def test_get_current_time_uses_current_time()->None:
    """Тест использования текущего времени"""
    with patch("src.views.datetime") as mock_datetime:
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = test_time
        result = get_current_time()
        assert "12:00:00" in result


def test_greeting_morning()->None:
    """Тест для утреннего приветствия (5:00-11:59)"""
    with patch("src.views.get_current_time", return_value="2023-01-01 08:30:00"):
        assert get_greeting() == "Доброе утро"


def test_greeting_afternoon()->None:
    """Тест для дневного приветствия (12:00-16:59)"""
    with patch("src.views.get_current_time", return_value="2023-01-01 14:15:00"):
        assert get_greeting() == "Добрый день"


def test_greeting_evening()->None:
    """Тест для вечернего приветствия (17:00-22:59)"""
    with patch("src.views.get_current_time", return_value="2023-01-01 19:45:00"):
        assert get_greeting() == "Добрый вечер"


def test_greeting_night()->None:
    """Тест для ночного приветствия (23:00-4:59)"""
    with patch("src.views.get_current_time", return_value="2023-01-01 03:20:00"):
        assert get_greeting() == "Доброй ночи"


@pytest.mark.parametrize(
    "time_str, expected",
    [
        ("04:59:59", "Доброй ночи"),
        ("05:00:00", "Доброе утро"),
        ("11:59:59", "Доброе утро"),
        ("12:00:00", "Добрый день"),
        ("16:59:59", "Добрый день"),
        ("17:00:00", "Добрый вечер"),
        ("22:59:59", "Добрый вечер"),
        ("23:00:00", "Доброй ночи"),
    ],
)
def test_greeting_boundary_times(time_str:str, expected:str)->None:
    """Параметризованный тест граничных значений"""
    with patch("src.views.get_current_time", return_value=f"2023-01-01 {time_str}"):
        assert get_greeting() == expected, f"Ошибка для времени {time_str}"


def test_process_cards_basic(basic_transactions)->None:
    """Тест базовой функциональности"""

    result = process_cards(basic_transactions)

    assert len(result) == 2  # Две уникальные карты
    assert result[0]["last_digits"] == "5678"
    assert result[0]["total_spent"] == 3000  # 1000 + 2000
    assert result[0]["cashback"] == 150  # 50 + 100
    assert result[1]["last_digits"] == "4321"
    assert result[1]["total_spent"] == 500
    assert result[1]["cashback"] == 25


def test_skip_invalid_cards(invalid_cards)->None:
    """Тест пропуска невалидных номеров карт"""

    result = process_cards(invalid_cards)

    assert len(result) == 1  # Только одна валидная карта
    assert result[0]["last_digits"] == "1234"
    assert result[0]["total_spent"] == 400


def test_positive_amounts_ignored()->None:
    """Тест игнорирования положительных сумм"""
    transactions = [
        {"Номер карты": "1111222233334444", "Сумма операции": 1000},
        # Положительная сумма
        {"Номер карты": "1111222233334444", "Сумма операции": -500},
    ]

    result = process_cards(transactions)

    assert result[0]["total_spent"] == 500


def test_short_card_numbers()->None:
    """Тест обработки коротких номеров карт"""
    transactions = [
        {"Номер карты": "123", "Сумма операции": -100},  # Номер короче 4 цифр
        {"Номер карты": "4567", "Сумма операции": -200},  # Ровно 4 цифры
    ]

    result = process_cards(transactions)

    assert result[0]["last_digits"] == "123"  # Берется весь номер
    assert result[1]["last_digits"] == "4567"  # Берется весь номер


def test_non_numeric_cashback()->None:
    """Тест обработки нечислового кэшбэка"""
    transactions = [
        {"Номер карты": "1111222233334444", "Сумма операции": -100, "Бонусы (включая кэшбэк)": "10"},  # Строка
        {"Номер карты": "1111222233334444", "Сумма операции": -200, "Бонусы (включая кэшбэк)": None},  # None
    ]

    result = process_cards(transactions)

    assert result[0]["cashback"] == 0  # Нечисловой кэшбэк игнорируется


def test_returns_correct_number_of_transactions() -> None:
    """Проверяет, что функция возвращает правильное количество транзакций"""
    transactions = [
        {"Сумма операции": -100, "Дата операции": "2023-01-01"},
        {"Сумма операции": -200, "Дата операции": "2023-01-02"},
        {"Сумма операции": -300, "Дата операции": "2023-01-03"},
    ]

    result = get_top_transactions(transactions, 2)
    assert len(result) == 2


def test_ignores_positive_amounts() -> None:
    """Проверяет, что положительные суммы игнорируются"""
    transactions = [
        {"Сумма операции": 100, "Дата операции": "2023-01-01"},
        # Должна быть проигнорирована
        {"Сумма операции": -200, "Дата операции": "2023-01-02"},
    ]

    result = get_top_transactions(transactions)
    assert len(result) == 1
    assert result[0]["amount"] == 200


def test_sorts_by_amount_descending() -> None:
    """Проверяет сортировку по убыванию суммы"""
    transactions = [
        {"Сумма операции": -300, "Дата операции": "2023-01-01"},
        {"Сумма операции": -100, "Дата операции": "2023-06-07"},
        {"Сумма операции": -200, "Дата операции": "2023-01-21"},
    ]

    result = get_top_transactions(transactions, n=3)
    assert result[0]["amount"] == 300
    assert result[1]["amount"] == 200
    assert result[2]["amount"] == 100


def test_handles_missing_fields() -> None:
    """Проверяет обработку отсутствующих полей"""
    transactions = [{"Сумма операции": -100}]  # Нет даты, категории и описания

    result = get_top_transactions(transactions)[0]
    assert result["date"] == ""
    assert result["category"] == ""
    assert result["description"] == ""


def test_default_n_value() -> None:
    """Проверяет, что по умолчанию возвращается 5 транзакций"""
    transactions = [{"Сумма операции": -i * 100} for i in range(10)]  # 10 транзакций

    result = get_top_transactions(transactions)  # Без указания n
    assert len(result) == 5


def test_success(mock_api: Mock) -> None:
    """Тест успешного получения курсов валют"""
    # Настраиваем мок для возврата тестовых данных
    mock_api.return_value = [{"currency": "USD", "exchange_rate": 90.5}]

    assert get_currency_rates() == [{"USD": 90.5}]
    mock_api.assert_called_once_with("rub", ("USD", "EUR", "CNY"))


def test_failure(mock_api: Mock) -> None:
    """Тест обработки ошибки API"""
    mock_api.return_value = None
    assert get_currency_rates() is None


def test_get_stock_prices_success(mock_finnhub: Mock) -> None:
    """Тест успешного получения цен акций через Finnhub."""
    mock_finnhub.return_value = [
        {"ticker": "MSFT", "current_price": 250.75},
        {"ticker": "AAPL", "current_price": 150.50},
    ]

    result = get_stock_prices()

    expected = [{"MSFT": 250.75}, {"AAPL": 150.50}]
    assert result == expected

    mock_finnhub.assert_called_once_with(("MSFT", "AAPL", "TSLA"))


def test_custom_tickers(mock_finnhub: Mock) -> None:
    """Тест работы с пользовательским списком тикеров."""
    mock_finnhub.return_value = [{"ticker": "GOOGL", "current_price": 125.25}]

    result = get_stock_prices(tickers=("GOOGL", "AMZN"))
    expected = [{"GOOGL": 125.25}]

    assert result == expected
    mock_finnhub.assert_called_once_with(("GOOGL", "AMZN"))


def test_empty_response(mock_finnhub: Mock) -> None:
    """Тест обработки пустого ответа от API."""
    mock_finnhub.return_value = []

    result = get_stock_prices()
    assert result == []


def test_malformed_data(mock_finnhub: Mock) -> None:
    """Тест обработки некорректных данных от API."""
    mock_finnhub.return_value = [
        {"wrong_field": "MSFT"},  # Невалидные данные
        {"ticker": "AAPL"},  # Нет цены
        {"ticker": "TSLA", "current_price": 700.50},  # Валидные данные
    ]
    result = get_stock_prices()
    assert result


def test_default_resource_used(mock_finnhub: Mock) -> None:
    """Тест использования ресурса по умолчанию (finnhub)."""
    mock_finnhub.return_value = [{"ticker": "MSFT", "current_price": 250.75}]

    result = get_stock_prices(resource="finnhub")  # Явно указываем ресурс
    assert len(result) == 1


def test_main_page_success(mock_dependencies: dict) -> None:
    """Тест успешного формирования главной страницы"""
    result = main_page()

    # Проверяем что результат является валидным JSON
    response = json.loads(result)

    assert response == {
        "greeting": "Добрый день",
        "cards": [{"card": "test"}],
        "top_transactions": [{"transaction": "test"}],
        "currency_rates": [{"USD": 90.5}],
        "stock_prices": [{"AAPL": 150.0}],
    }

    # Проверяем вызовы зависимостей
    mock_dependencies["mock_reader"].assert_called_once_with("data/operations.xlsx")
    mock_dependencies["mock_greeting"].assert_called_once()
    mock_dependencies["mock_cards"].assert_called_once_with([{"test": "data"}])
    mock_dependencies["mock_top"].assert_called_once_with([{"test": "data"}], 5)
    mock_dependencies["mock_rates"].assert_called_once()
    mock_dependencies["mock_stocks"].assert_called_once()


def test_main_page_empty_data(mock_dependencies: dict) -> None:
    """Тест обработки пустых данных"""
    mock_dependencies["mock_reader"].return_value = []
    mock_dependencies["mock_cards"].return_value = []
    mock_dependencies["mock_top"].return_value = []

    result = main_page()
    response = json.loads(result)

    assert response == {
        "greeting": "Добрый день",
        "cards": [],
        "top_transactions": [],
        "currency_rates": [{"USD": 90.5}],
        "stock_prices": [{"AAPL": 150.0}],
    }
