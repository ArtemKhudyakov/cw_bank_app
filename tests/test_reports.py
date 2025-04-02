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
    assert len(result) == 1
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


# @pytest.mark.parametrize(
#     "transactions, test_case_name, expected_results",
#     [
#         (
#                 [
#                     {"Дата операции": "01.01.2023", "Категория": "Супермаркеты", "Сумма операции": -1000},
#                     {"Дата операции": "15.01.2023", "Категория": "Кафе", "Сумма операции": -500},
#                     {"Дата операции": "01.03.2023", "Категория": "Супермаркеты", "Сумма операции": -1500},
#                     {"Дата операции": "10.04.2023", "Категория": "Транспорт", "Сумма операции": -200},
#                 ],
#                 "base_case",
#                 {
#                     "total_spent": 3200,
#                     "categories": ["Супермаркеты", "Кафе", "Транспорт"],
#                     "supermarket_total": 2500,
#                     "dates": [
#                         datetime(2023, 1, 1),
#                         datetime(2023, 1, 15),
#                         datetime(2023, 3, 1),
#                         datetime(2023, 4, 10)
#                     ]
#                 }
#         ),
#         (
#                 [
#                     {"Дата операции": "05.05.2023", "Категория": "АЗС", "Сумма операции": -3000},
#                     {"Дата операции": "20.05.2023", "Категория": "Ресторан", "Сумма операции": -2500},
#                 ],
#                 "few_transactions",
#                 {
#                     "total_spent": 5500,
#                     "categories": ["АЗС", "Ресторан"],
#                     "supermarket_total": 0,
#                     "dates": [
#                         datetime(2023, 5, 5),
#                         datetime(2023, 5, 20)
#                     ]
#                 }
#         ),
#         (
#                 [],
#                 "empty_case",
#                 {
#                     "total_spent": 0,
#                     "categories": [],
#                     "supermarket_total": 0,
#                     "dates": []
#                 }
#         ),
#         (
#                 [
#                     {"Дата операции": "01.06.2023", "Категория": "Супермаркеты", "Сумма операции": -500},
#                     {"Дата операции": "02.06.2023", "Категория": "Супермаркеты", "Сумма операции": -700},
#                     {"Дата операции": "03.06.2023", "Категория": "Супермаркеты", "Сумма операции": -300},
#                 ],
#                 "single_category",
#                 {
#                     "total_spent": 1500,
#                     "categories": ["Супермаркеты"],
#                     "supermarket_total": 1500,
#                     "dates": [
#                         datetime(2023, 6, 1),
#                         datetime(2023, 6, 2),
#                         datetime(2023, 6, 3)
#                     ]
#                 }
#         )
#     ],
#     ids=["base_case", "few_transactions", "empty_case", "single_category"]
# )
# def test_process_transactions(transactions, test_case_name, expected_results):
#     """Тест обработки транзакций с различными сценариями"""
#     # Создаем DataFrame из тестовых данных
#     df = pd.DataFrame(transactions)
#
#     # Для пустого DataFrame создаем колонки вручную
#     if df.empty:
#         df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма операции"])
#
#     # Преобразуем даты из строк в datetime
#     if not df.empty and 'Дата операции' in df.columns:
#         df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y')
#
#     # 1. Проверка общей суммы расходов
#     total_spent = abs(df['Сумма операции'].sum()) if 'Сумма операции' in df.columns else 0
#     assert total_spent == expected_results['total_spent']
#
#     # 2. Проверка уникальных категорий
#     categories = df['Категория'].unique().tolist() if not df.empty and 'Категория' in df.columns else []
#     assert sorted(categories) == sorted(expected_results['categories'])
#
#     # 3. Проверка суммы по категории "Супермаркеты"
#     supermarket_total = 0
#     if not df.empty and 'Категория' in df.columns and 'Сумма операции' in df.columns:
#         if 'Супермаркеты' in df['Категория'].values:
#             supermarket_total = abs(df[df['Категория'] == 'Супермаркеты']['Сумма операции'].sum())
#     assert supermarket_total == expected_results['supermarket_total']
#
#     # 4. Проверка дат операций (обновленный способ без предупреждений)
#     dates = []
#     if not df.empty and 'Дата операции' in df.columns:
#         dates = df['Дата операции'].dt.to_pydatetime().tolist() if pd.__version__ < '2.0.0' else df[
#             'Дата операции'].dt.to_list()
#     assert dates == expected_results['dates']
