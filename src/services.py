import logging
import os
import pathlib as p
import re
from datetime import datetime
from typing import Any, Dict, List


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
file_handler = logging.FileHandler(f"{project_root_path}/logs/{module_name}.log", encoding="utf-8", mode="w")
file_formater = logging.Formatter("%(asctime)s - %(name)s -%(funcName)s - %(lineno)d - %(levelname)s -" " %(message)s")
file_handler.setFormatter(file_formater)
logger.addHandler(file_handler)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Рассчитывает сумму для инвесткопилки через округление трат за указанный месяц. Принимает месяц строго в
    формате 'YYYY-MM' (например '2021-12'), список транзакций, шаг округления (10, 50, 100 и т.д.).
    Возвращает сумму для инвесткопилки на заданный месяц с указанным шагом округления"""

    logger.info(f"Начало расчета инвесткопилки для месяца: {month} с шагом {limit}")

    # Валидация формата месяца
    try:
        logger.debug("Проверка формата месяца")
        if not re.fullmatch(r"^\d{4}-\d{2}$", month):
            raise ValueError("Месяц должен быть в формате YYYY-MM (например: '2021-12')")

        year, month_num = map(int, month.split("-"))
        if month_num < 1 or month_num > 12:
            raise ValueError("Номер месяца должен быть от 01 до 12")

    except ValueError as e:
        logger.error(f"Ошибка валидации месяца: {e}")
        raise
    except Exception:
        logger.exception("Непредвиденная ошибка при валидации месяца")
        raise ValueError("Неверный формат месяца")

    # Валидация шага округления
    if limit <= 0:
        logger.warning(f"Некорректный шаг округления: {limit}. Возвращаем 0.0")
        return 0.0

    total_saved = 0.0
    processed_count = 0
    skipped_count = 0

    logger.info(f"Начало обработки {len(transactions)} транзакций")

    for t in transactions:
        try:
            # Проверка структуры транзакции
            if not isinstance(t, dict):
                skipped_count += 1
                logger.debug("Пропуск: транзакция не является словарем")
                continue

            if not all(k in t for k in ["Дата операции", "Сумма операции"]):
                skipped_count += 1
                logger.debug(f"Пропуск транзакции: отсутствуют обязательные поля. Транзакция: {t}")
                continue

            # Проверка типа и знака суммы
            amount = t["Сумма операции"]
            if not isinstance(amount, (int, float)):
                skipped_count += 1
                logger.debug(f"Пропуск: нечисловая сумма операции: {amount}")
                continue

            if amount >= 0:
                skipped_count += 1
                logger.debug(f"Пропуск: пополнение на сумму {amount}")
                continue

            # Парсинг даты операции
            try:
                date_str = str(t["Дата операции"])[:10]
                transaction_date = datetime.strptime(date_str, "%d.%m.%Y")
                transaction_month = transaction_date.strftime("%Y-%m")
                logger.debug(f"Успешно распарсена дата: {date_str} -> {transaction_month}")
            except Exception as e:
                skipped_count += 1
                logger.warning(f"Ошибка парсинга даты: {e}. Транзакция: {t}")
                continue

            # Проверка соответствия месяца
            if transaction_month != month:
                skipped_count += 1
                logger.debug(f"Пропуск: транзакция за {transaction_month} не соответствует целевому месяцу {month}")
                continue

            amount_abs = abs(amount)
            if amount_abs % limit == 0:  # Если сумма уже кратна шагу
                difference = 0.0
            else:
                rounded_amount = ((amount_abs // limit) + 1) * limit
                difference = rounded_amount - amount_abs

            total_saved += difference

            logger.debug(
                f"Обработана транзакция: сумма {amount_abs} -> округлено до {rounded_amount} (+{difference:.2f})"
            )

        except Exception as e:
            skipped_count += 1
            logger.exception(f"Критическая ошибка обработки транзакции: {e}. Транзакция: {t}")
            continue

    logger.info(
        f"Обработка завершена. Успешно: {processed_count}, "
        f"пропущено: {skipped_count}, Итоговая сумма: {total_saved:.2f}"
    )

    return round(total_saved, 2)


#
# transactions = list(data_reader.xlsx_reader())
# for i, t in enumerate(transactions):
#     if i <10:
#         print(t)
# invest = investment_bank("2021-12", transactions, 100)
# print(invest)
