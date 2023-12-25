#Logging.py

import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Создаем логгер
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Создаем форматтер
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Создаем файловый обработчик логов
    file_handler = RotatingFileHandler('cartoons.log', maxBytes=5*1024*1024, backupCount=2)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)

    return logger
