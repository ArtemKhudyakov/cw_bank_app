from src.data_reader import xlsx_reader
from src.reports import spending_by_category
from src.services import investment_bank
from src.utils import (
    get_greeting,
    get_current_time,
    process_cards,
    get_currency_rates,
    get_stock_prices,
    get_top_transactions
)
from src.views import main_page


def main() -> None:
    transactions = xlsx_reader("data/operations.xlsx")
    print(get_greeting())
    print("Давайте проверим работоспособность всех функций")
    while True:
        func_numb = input(
            """\nДля проверки работоспособности функции введите ее номер в соответствии со списком:
        1. Функция 'get_current_time()' вывода текущей даты и времени.
        2. Функция 'get_greeting' вывода приветствия.
        3. Функция 'process_cards' обработки данных банковских карт.
        4. Функция 'get_top_transactions' выводит топ транзакций.
        5. Функция 'get_currency_rates' возвращает актуальные курсы валют по отношению к рублю.
        6. Функция 'get_stock_prices' возвращает цены акций из S&P500.
        7. Функция 'investment_bank' рассчитывает сумму для инвесткопилки через округление трат за указанный месяц.
        8. Функция 'report_to_file' возвращает траты по заданной категории за последние 3 месяца с указанной даты.
        9. Функция 'main_page' функция, обрабатывающая данные и возвращающая JSON-ответ для страницы главная.
        Для выхода из программы введите 'quit'
        """
        )

        if func_numb == "1":
            print(get_current_time())
        elif func_numb == "2":
            print(get_greeting())
        elif func_numb == "3":
            print(process_cards(transactions))
        elif func_numb == "4":
            try:
                n = int(input("\nВведите количество N-топ транзакций\n-->"))
                print(get_top_transactions(transactions, n))
            except Exception as e:
                print(e)
        elif func_numb == "5":
            print(get_currency_rates())
        elif func_numb == "6":
            tickers = input("Введите тикеры акций через запятую (Пример: MSFT, AAPL, TSLA)")
            tickers_list = tuple(tickers.upper().split(", "))
            print(get_stock_prices("finnhub", tickers_list))
        elif func_numb == "7":
            try:
                month = input("Введите месяц для расчета кэшбэка (Пример: '2021-12')")
                limit = int(input("Введите шаг округления (10, 50, 100 и т.д.)"))
                print(
                    f"""Сумма в инвесткопилку за указанный месяц составила бы
    {investment_bank(month, transactions, limit)}"""
                )
            except Exception as e:
                print(e)
        elif func_numb == "8":
            try:
                category = input("Введите наименование категории (Пример: Супермаркеты)")
                target_date = input("Введите дату (Пример: 2021-12-01)")
                print(spending_by_category(transactions, category, target_date))
            except Exception as e:
                print(e)
        elif func_numb == "9":
            print(main_page())
        elif func_numb == "quit":
            break
        else:
            print("Команда нераспознана")


if __name__ == "__main__":
    main()
