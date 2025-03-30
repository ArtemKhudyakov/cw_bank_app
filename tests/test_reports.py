import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from src.reports import MOSCOW_TZ, report_to_file, spending_by_category


def test_spending_by_category_with_dataframe(
    data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Тестирует работу функции с DataFrame на входе."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    result = spending_by_category(data_dataframe, "Супермаркеты", "2023-04-10")
    assert len(result) == 1
    assert all(result["Категория"].str.lower() == str("супермаркеты"))
    assert all(result["Сумма операции"] > 0)


def test_spending_by_category_with_list(
    data_list: List[Dict[str, Any]], monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Тестирует работу функции со списком словарей на входе."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    result = spending_by_category(data_list, "супермаркеты")
    assert len(result) == 2
    assert all(result["Сумма операции"] > 0)


def test_spending_by_category_date_formatting(
    data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Тестирует форматирование дат в результате."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    result = spending_by_category(data_dataframe, "Супермаркеты")
    assert result["Дата операции"].str.contains(r"\d{2}\.\d{2}\.\d{4} \(UTC \+3\)").all()


def test_spending_by_category_missing_columns(
    data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Тестирует обработку отсутствия обязательных колонок."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    with pytest.raises(ValueError):
        spending_by_category(data_dataframe.drop(columns=["Категория"]), "Супермаркеты")


def test_spending_by_category_empty_result(
    data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Тестирует обработку несуществующей категории."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    result = spending_by_category(data_dataframe, "Несуществующая категория")
    assert len(result) == 0


def test_report_to_file_default_name(tmp_path: Path, monkeypatch: MonkeyPatch, data_dataframe: pd.DataFrame) -> None:
    """Тестирует декоратор report_to_file с именем файла по умолчанию."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    spending_by_category(data_dataframe, "Супермаркеты", "2023-03-10")

    json_files = list(tmp_path.glob("json_reports/report_*.json"))
    assert len(json_files) == 1

    with open(json_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 2


def test_report_to_file_with_custom_name(
    tmp_path: Path, monkeypatch: MonkeyPatch, data_dataframe: pd.DataFrame
) -> None:
    """Тестирует декоратор report_to_file с кастомным именем файла."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)

    @report_to_file("custom_report")
    def test_func() -> pd.DataFrame:
        return data_dataframe

    test_func()

    assert (tmp_path / "json_reports" / "custom_report.json").exists()


def test_timezone_handling(data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Тестирует обработку временных зон."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    result = spending_by_category(data_dataframe, "Супермаркеты", "2023-04-10")

    test_date = MOSCOW_TZ.localize(datetime(2023, 4, 10))
    three_months_ago = test_date - timedelta(days=90)

    date_strings = result["Дата операции"].str.extract(r"(\d{2}\.\d{2}\.\d{4})")[0]
    result_dates = pd.to_datetime(date_strings, dayfirst=True).dt.tz_localize(MOSCOW_TZ)

    assert all((result_dates >= three_months_ago) & (result_dates <= test_date))


def test_timezone_handling_now(data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    """Тестирует фильтрацию по текущей дате."""
    monkeypatch.setattr("src.reports.project_root_path", tmp_path)
    result = spending_by_category(data_dataframe, "Супермаркеты")

    current_date = datetime.now(MOSCOW_TZ)
    three_months_ago = current_date - timedelta(days=90)

    date_strings = result["Дата операции"].str.extract(r"(\d{2}\.\d{2}\.\d{4})")[0]
    result_dates = pd.to_datetime(date_strings, dayfirst=True).dt.tz_localize(MOSCOW_TZ)

    assert all(result_dates >= three_months_ago)


def test_error_logging(
    caplog: LogCaptureFixture, data_dataframe: pd.DataFrame, monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    """Тестирует логирование ошибок."""
    try:
        spending_by_category(data_dataframe.drop(columns=["Дата операции"]), "Супермаркеты")
    except ValueError:
        pass

    assert "Отсутствуют обязательные колонки" in caplog.text
