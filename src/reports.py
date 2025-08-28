import json
import logging
import os
import pathlib as p
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import pytz

# Получаем имя модуля
module_name = p.Path(__file__).stem

# Путь к корневой папке
current_file_path = p.Path(__file__).resolve()
project_root_path = current_file_path.parent.parent

# Путь к папке "logs"
logs_dir = project_root_path / "logs"

# Создаем папку logs если её нет
os.makedirs(logs_dir, exist_ok=True)


# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f"{logs_dir}/{module_name}.log", encoding="utf-8", mode="w")
file_formater = logging.Formatter("%(asctime)s - %(name)s -%(funcName)s - %(lineno)d - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formater)
logger.addHandler(file_handler)

# Настраиваем московскую временную зону (UTC+3)
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


def get_moscow_time(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Получает текущее время UTC+3 (по умолчанию 'ГГГГ-ММ-ДД ЧЧ:ММ:СС')"""

    moscow_time = datetime.now(MOSCOW_TZ)
    return moscow_time.strftime(fmt)


def report_to_file(func_or_filename: Optional[Union[Callable, str]] = None) -> Callable:
    """Декоратор для сохранения отчетов в файл"""

    def decorator(report_func: Callable) -> Callable:
        @wraps(report_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = report_func(*args, **kwargs)

            # Путь к папке "json_reports_dir"
            json_reports_dir = project_root_path / "json_reports"
            os.makedirs(json_reports_dir, exist_ok=True)

            # Определяем имя файла
            if isinstance(func_or_filename, str):
                # Если передан параметр - используем его как имя файла
                file_name = f"{func_or_filename}.json"
            else:
                # Иначе - генерируем имя по умолчанию
                file_name = f"report_{report_func.__name__}_{get_moscow_time('%Y-%m-%d_%H-%M-%S')}.json"

            try:
                with open(f"{json_reports_dir}/{file_name}", "w", encoding="utf-8") as f:
                    if isinstance(result, (pd.DataFrame, pd.Series)):
                        result.to_json(f, orient="records", force_ascii=False, indent=4)
                    else:
                        json.dump(result, f, ensure_ascii=False, indent=4)
                logger.info(f"Отчет сохранен в файл: {file_name}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении отчета: {e}")
                raise

            return result

        return wrapper

    if callable(func_or_filename):
        return decorator(func_or_filename)
    return decorator


@report_to_file
def spending_by_category(
    transactions: Union[pd.DataFrame, List[Dict[str, Any]]], category: str, target_date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает траты по заданной категории за последние 3 месяца с указанной даты.
    Даты форматируются в виде 'DD.MM.YYYY (UTC +3)'"""

    logger.info(f"Формирование отчета по категории '{category.capitalize()}'")

    try:
        # Преобразуем в DataFrame если передан список словарей
        if isinstance(transactions, list):
            transactions_df = pd.DataFrame(transactions)
        else:
            transactions_df = transactions.copy()

        # Проверяем необходимые колонки
        required_columns = {"Дата операции", "Категория", "Сумма операции"}
        if not required_columns.issubset(transactions_df.columns):
            missing = required_columns - set(transactions_df.columns)
            raise ValueError(f"Отсутствуют обязательные колонки: {missing}")

        # Преобразуем дату операции в datetime с учетом временной зоны
        transactions_df["Дата операции"] = pd.to_datetime(
            transactions_df["Дата операции"], dayfirst=True
        ).dt.tz_localize(MOSCOW_TZ)

        # Определяем диапазон дат
        # current_date = None
        if target_date is None:
            current_date = datetime.now(MOSCOW_TZ)
        else:
            current_date = MOSCOW_TZ.localize(datetime.strptime(target_date, "%Y-%m-%d"))
        three_months_ago = current_date - timedelta(days=90)

        # Фильтрация данных
        mask = (
            (transactions_df["Категория"].str.lower().fillna("") == category.lower().strip())
            & (transactions_df["Дата операции"] >= three_months_ago)
            & (transactions_df["Дата операции"] <= current_date)
            & (transactions_df["Сумма операции"].astype(float) < 0)
        )

        result = transactions_df.loc[mask].copy()
        result["Сумма операции"] = result["Сумма операции"].abs()

        # Форматируем дату для вывода
        result["Дата операции"] = result["Дата операции"].dt.strftime("%d.%m.%Y (UTC +3)")

        logger.info(f"Найдено {len(result)} транзакций")
        return result.sort_values("Дата операции", ascending=False)

    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        raise


# from data_reader import xlsx_reader
#
# transactions = xlsx_reader()
# spending_by_category(transactions, "Супермаркеты", target_date="2020-03-01")
