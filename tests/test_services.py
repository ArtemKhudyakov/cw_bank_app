from typing import Any, Dict, List

import pytest
from pytest_mock import MockerFixture

from src.services import investment_bank


def test_invalid_month_format() -> None:
    with pytest.raises(ValueError, match="Месяц должен быть в формате YYYY-MM"):
        investment_bank("2021/12", [], 100)

    with pytest.raises(ValueError, match="Номер месяца должен быть от 01 до 12"):
        investment_bank("2021-13", [], 100)


def test_invalid_limit(sample_transactions: List[Dict[str, Any]]) -> None:
    assert investment_bank("2021-12", sample_transactions, 0) == 0.0
    assert investment_bank("2021-12", sample_transactions, -10) == 0.0


def test_correct_calculation(sample_transactions: List[Dict[str, Any]]) -> None:
    result = investment_bank("2021-12", sample_transactions, 50)
    expected = (200 - 160.89) + (100 - 64) + (50 - 7.07)
    assert round(result, 2) == round(expected, 2)

    result = investment_bank("2021-12", sample_transactions, 100)
    expected = (200 - 160.89) + (100 - 64) + (100 - 7.07)
    assert round(result, 2) == round(expected, 2)


def test_empty_transactions() -> None:
    assert investment_bank("2021-12", [], 100) == 0.0


def test_ignore_other_months(sample_transactions2: List[Dict[str, Any]]) -> None:
    """Проверяем что транзакции за другие месяцы игнорируются"""
    result = investment_bank("2021-12", sample_transactions2, 100)
    expected = 39.11 + 36.0
    assert round(result, 2) == round(expected, 2)

    november_result = investment_bank("2021-11", sample_transactions2, 100)
    assert november_result == 0.0


def test_skip_invalid_transactions(sample_transactions: List[Dict[str, Any]]) -> None:
    result = investment_bank("2021-12", sample_transactions, 10)
    assert result > 0


def test_rounding_precision() -> None:
    transactions = [
        {"Дата операции": "31.12.2021 00:00:00", "Сумма операции": -1.234},
        {"Дата операции": "31.12.2021 00:00:00", "Сумма операции": -5.678},
    ]
    result = investment_bank("2021-12", transactions, 1)
    assert result == 1.09


def test_logging(mocker: MockerFixture, sample_transactions: List[Dict[str, Any]]) -> None:
    mock_logger = mocker.patch("src.services.logger")
    investment_bank("2021-12", sample_transactions, 100)

    assert mock_logger.info.called
    assert mock_logger.debug.called
    assert any("Обработка завершена" in str(call) for call in mock_logger.info.call_args_list)
