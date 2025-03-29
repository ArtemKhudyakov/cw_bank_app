import json
import logging
import os
import pathlib as p

import src.data_reader as data_reader
from src.utils import get_currency_rates, get_greeting, get_stock_prices, get_top_transactions, process_cards

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


def main_page() -> str:
    """Главная функция, обрабатывающая данные и возвращающая JSON-ответ"""
    # Парсим входные данные
    logger.info("Запуск main_page")

    try:
        logger.debug("Чтение данных из XLSX")
        data = data_reader.xlsx_reader("data/operations.xlsx")

        response = {
            "greeting": get_greeting(),
            "cards": process_cards(data),
            "top_transactions": get_top_transactions(data, 5),
            "currency_rates": get_currency_rates(),
            "stock_prices": get_stock_prices(),
        }

        logger.debug("Формирование JSON-ответа")
        json_response = json.dumps(response, ensure_ascii=False, indent=4)
        logger.info("Успешное завершение main_page")
        return json_response
    except Exception as e:
        logger.critical(f"Критическая ошибка в main_page: {e}")
        return json.dumps({"error": "Internal Server Error"}, ensure_ascii=False, indent=4)


print(main_page())
