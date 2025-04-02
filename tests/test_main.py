import unittest
from unittest.mock import patch, MagicMock
import io
import sys

# Мокаем модули до импорта
sys.modules['utils'] = MagicMock()
sys.modules['views'] = MagicMock()
sys.modules['services'] = MagicMock()
sys.modules['reports'] = MagicMock()
sys.modules['data_reader'] = MagicMock()

# Импортируем main после мокинга
from src.main import main


class TestMainFunction(unittest.TestCase):
    def setUp(self):
        # Получаем наши моки
        self.mock_utils = sys.modules['utils']
        self.mock_views = sys.modules['views']
        self.mock_services = sys.modules['services']
        self.mock_reports = sys.modules['reports']
        self.mock_data_reader = sys.modules['data_reader']

        # Настраиваем возвращаемые значения для моков
        self.test_transactions = [
            {'Дата операции': '2021-12-01', 'Сумма операции': 100, 'Категория': 'Супермаркеты'},
            {'Дата операции': '2021-12-02', 'Сумма операции': 200, 'Категория': 'Рестораны'}
        ]

        self.mock_data_reader.xlsx_reader.return_value = self.test_transactions
        self.mock_utils.get_greeting.return_value = "Добро пожаловать!"
        self.mock_utils.get_current_time.return_value = "2021-12-01 12:00:00"
        self.mock_utils.process_cards.return_value = "Обработанные карты"
        self.mock_utils.get_currency_rates.return_value = {"USD": 75.0}
        self.mock_utils.get_stock_prices.return_value = {"AAPL": 150.0}
        self.mock_services.investment_bank.return_value = 1000
        self.mock_reports.spending_by_category.return_value = "Отчет по категории"
        self.mock_views.main_page.return_value = {"data": "Главная страница"}

        # Мок для отдельно импортируемой функции
        self.mock_utils.get_top_transactions.return_value = "Топ 5 транзакций"

    @patch('builtins.input', side_effect=['1', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_1_current_time(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("2021-12-01 12:00:00", output)

    @patch('builtins.input', side_effect=['2', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_2_greeting(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Добро пожаловать!", output)

    @patch('builtins.input', side_effect=['3', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_3_process_cards(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Обработанные карты", output)

    @patch('builtins.input', side_effect=['5', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_5_currency_rates(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("{'USD': 75.0}", output)

    @patch('builtins.input', side_effect=['6', 'AAPL, MSFT', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_6_stock_prices(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("{'AAPL': 150.0}", output)

    @patch('builtins.input', side_effect=['7', '2021-12', '100', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_7_investment_bank(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("1000", output)

    @patch('builtins.input', side_effect=['8', 'Супермаркеты', '2021-12-01', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_8_spending_report(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Отчет по категории", output)

    @patch('builtins.input', side_effect=['9', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_function_9_main_page(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Главная страница", output)

    @patch('builtins.input', side_effect=['invalid', 'quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_invalid_input(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Команда нераспознана", output)

    @patch('builtins.input', side_effect=['quit'])
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_quit_command(self, mock_stdout, mock_input):
        main()
        output = mock_stdout.getvalue()
        self.assertNotIn("Команда нераспознана", output)
        self.assertIn("Добро пожаловать!", output)  # Проверяем что greeting был
