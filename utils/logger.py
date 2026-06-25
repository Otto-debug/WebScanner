import logging
import sys
from datetime import datetime
from pathlib import Path

# Папка проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Папка с логами
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Полный путь до файла
LOG_FILE = LOG_DIR / "scanner.log"

# Единый формат для всех логов
LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name='web_scanner', log_file=LOG_FILE, level=logging.INFO):
    """
    Настройка логгера. Если логгер уже существует то просто возвращает его
    """
    logger = logging.getLogger(name)

    # Если у логгера уже есть хендлер, значит он уже настроен
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Форматтер для единообразного вывода
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Хендлер для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Хендлер для записи в файл
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()