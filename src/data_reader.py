import pathlib as p
from typing import Any, Dict, List

import pandas as pd


def xlsx_reader(
    path_to_xlsx_file: str = "data/operations.xlsx",
) -> List[Dict[str, Any]]:
    """Функция принимает путь до файла данных формата xlsx, и возвращает список
    словарей"""
    current_file_path = p.Path(__file__).resolve()
    project_root_path = current_file_path.parent.parent
    file_path = f"{project_root_path}/{path_to_xlsx_file}"
    try:
        excel_data = pd.read_excel(file_path)
        data_list = excel_data.to_dict(orient="records")
        return [{str(key): value for key, value in item.items()} for item in data_list]
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        raise


# data = list(xlsx_reader())
# for i, t in enumerate(data):
#     if i <10:
#         print(t)
