import json

from src.views import main_page


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
