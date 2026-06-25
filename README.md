# WebScanner — XSS-сканер для OWASP Juice Shop

Автоматизированный сканер уязвимостей типа XSS (Reflected, Stored, HTML Injection, Attribute Injection), написанный на Python с использованием Selenium и Requests. Сканер тестирует локально развёрнутое (через Docker) демо-приложение [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) — намеренно уязвимое веб-приложение, созданное для практики в области безопасности.

> ⚠️ Проект находится в разработке. Часть функциональности (см. раздел «Структура проекта») пока не подключена к основному сценарию запуска.

## Возможности

Сканер автоматически проверяет следующие векторы:

- **Reflected XSS** в поисковой строке
- **Stored XSS** в отзывах на товары (review)
- **Stored Reflection** в имени профиля пользователя
- **Stored XSS через изображение профиля** (SVG-payload с `onload`)
- **Reflected XSS** в ответе на секретный вопрос при регистрации
- **Stored XSS / HTML Injection / Attribute Injection** в сохранённых способах оплаты

Дополнительно:

- Логирование всех действий и найденных уязвимостей (`logs/scanner.log`)
- Сводный отчёт по найденным уязвимостям после прохода всех тестов (`print_summary`)

## Стек технологий

- **Python**
- **Selenium** (управление браузером Chrome в headless-режиме)
- **Requests** (регистрация пользователей через API Juice Shop)

## Структура проекта

```
WebScanner/
├── logs/
│   └── scanner.log              # логи работы сканера
├── scanner/
│   ├── __init__.py
│   └── juice_shop_selenium_scanner.py   # основной класс сканера (ScannerJuiceShopXSS)
├── utils/
│   ├── __init__.py
│   └── logger.py                 # настройка логгера
├── crawler.py                    # пока не используется в текущей версии
├── juice_shop_crawler.py         # пока не используется в текущей версии
├── text                          # вспомогательный файл, не задействован
├── requirements.txt
└── main.py
```

## Требования

- Python 3.9+
- Google Chrome
- Chromedriver (путь к бинарю задан в коде как `/usr/bin/chromedriver` — при необходимости измените путь в `ScannerJuiceShopXSS.__init__`)
- Docker (для запуска тестового стенда Juice Shop)

## Установка

```bash
git clone https://github.com/Otto-debug/WebScanner.git
cd WebScanner
pip install -r requirements.txt
```

Убедитесь, что Chrome и chromedriver установлены и их версии совпадают.

## Запуск тестового стенда (Juice Shop)

Сканер рассчитан на работу с Juice Shop, поднятым локально на `http://localhost:3000`:

```bash
docker run --rm -p 3000:3000 bkimminich/juice-shop
```

## Запуск сканера

Запускайте из корневой директории проекта, чтобы корректно работал импорт `utils.logger`:

```bash
python -m scanner.juice_shop_selenium_scanner
```

> Если точкой входа у вас служит `main.py` — используйте `python main.py`; при необходимости поправьте команду под вашу структуру запуска.

По умолчанию браузер запускается в headless-режиме (`ScannerJuiceShopXSS(headless=True)`). Чтобы видеть процесс сканирования в открытом окне браузера, передайте `headless=False`.

## Логи и отчёт

- Подробный лог выполнения пишется в `logs/scanner.log`.
- После завершения всех тестов (`run_all`) в консоль и лог выводится сводка найденных уязвимостей: тип, URL, параметр и использованный payload.

## ⚠️ Дисклеймер

Сканер предназначен **только** для тестирования на специально предоставленных или собственных тестовых стендах (например, локально развёрнутом Juice Shop). Не используйте его против сайтов и систем, на тестирование которых у вас нет явного разрешения.

