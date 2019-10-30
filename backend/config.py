import os

SEPARATOR = '*' * 50
JSON_COURSES_PATH = os.path.abspath('courses.json')
MAIN_PATH = os.path.abspath('GeekBrains')
MAIN_URL = "https://geekbrains.ru"
COURSES_URL = "https://geekbrains.ru/education"
MAIN_MENU = [
    SEPARATOR,
    '1 - Пропарсить и сохранить в json',
    f'2 - Скачать из json (файл должен находится по пути: {COURSES_URL})',
    '3 - Пропарсить и скачать (удаляется json файл)',
    '4 - Пропарсить и скачать (сохранить json файл)',
    '5 - Выйти\n',
    'PS: Для скачивания материала может потребоваться много времени \
и места на жестком диске',
    ]
ERROR_MESSAGES = [
    SEPARATOR,
    f"Не удается скачать ссылки на уроки с основной страницы {COURSES_URL}, \
возможные проблемы:",
    "1. Нет подключения к интернету",
    "2. Не верный логин и/или пароль от GB",
    "3. GB что то переделали на сайте, и надо редактировать скрипт",
    ]
