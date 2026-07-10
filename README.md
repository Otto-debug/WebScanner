# WebScanner — XSS-сканер для OWASP Juice Shop

Автоматизированный сканер уязвимостей типа XSS (Reflected, Stored, HTML Injection, Attribute Injection), написанный на Python с использованием Selenium и Requests. Сканер тестирует локально развёрнутое (через Docker) демо-приложение [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) — намеренно уязвимое веб-приложение, созданное для практики в области безопасности.

Помимо XSS, данный инструмент включает модуль для автоматизированного поиска SQL-инъекций (SQLi) в различных API-эндпоинтах Juice Shop, работающий на основе библиотеки Requests и не требующий браузера.
> ⚠️ Проект находится в разработке. Часть функциональности (см. раздел «Структура проекта») пока не подключена к основному сценарию запуска.

## Возможности

Сканер автоматически проверяет следующие векторы:
### XSS
- **Reflected XSS** в поисковой строке
- **Stored XSS** в отзывах на товары (review)
- **Stored Reflection** в имени профиля пользователя
- **Stored XSS через изображение профиля** (SVG-payload с `onload`)
- **Reflected XSS** в ответе на секретный вопрос при регистрации
- **Stored XSS / HTML Injection / Attribute Injection** в сохранённых способах оплаты

### SQL Injection
- **Error-based / Union-based SQLi** в поиске товаров (`/rest/products/search`)
- **SQLi в логине** (`/rest/user/login`)
- **SQLi при регистрации** (`/api/Users`)
- **SQLi в отзывах** (`/api/Feedbacks`)
- **SQLi в адресах** (`/api/Addresss`)
- **SQLi в способах оплаты** (`/api/Cards`)
- **SQLi в заявках на утилизацию** (`/api/Recycles`)
- **SQLi в path-параметрах** (трекинг заказа `/rest/track-order/{id}`, получение продукта `/api/Products/{id}`)
- **Обнаружение Blind Time-based SQLi**, обхода аутентификации, аномального размера ответа.

Дополнительно:

- Логирование всех действий и найденных уязвимостей (`logs/scanner.log`)
- Сводный отчёт по найденным уязвимостям после прохода всех тестов (`print_summary`)

## Стек технологий

- **Python**
- **Selenium** (управление браузером Chrome в headless-режиме) – для XSS
- **Requests** (регистрация пользователей, API-запросы) – для XSS и SQLi
- **Библиотеки:** `uuid`, `random`, `string`, `re`, `urllib.parse`

## Структура проекта

```
WebScanner/
├── logs/
│ └── scanner.log # логи работы сканера
├── models/
│ ├── init.py
│ └── vulnerability.py # модель для хранения информации об уязвимости
├── scanner/
│ ├── init.py
│ ├── juice_shop_selenium_scanner.py # XSS сканер (Selenium)
│ └── sqli_juice_shop.py # SQLi сканер (Requests)
├── utils/
│ ├── init.py
│ ├── logger.py # настройка логгера
│ ├── severity.py # классификация severity и CWE для SQLi
│ └── sqli_payloads.py # набор payload'ов для SQLi
├── .gitignore
├── README.md
└── requirements.txt
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

### XSS
```bash
python -m scanner.juice_shop_selenium_scanner
```
По умолчанию браузер запускается в headless-режиме (`ScannerJuiceShopXSS(headless=True)`). Чтобы видеть процесс сканирования в открытом окне браузера, передайте `headless=False`.
### SQLi
```bash
python -m scanner.sqli_juice_shop
```
Сканер использует HTTP-запросы (библиотека Requests) и не требует открытого браузера. Все результаты логируются в logs/scanner.log и выводятся в консоль по окончании работы.

> Если точкой входа у вас служит `main.py` — используйте `python main.py`; при необходимости поправьте команду под вашу структуру запуска.

## Логи и отчёт

- Подробный лог выполнения пишется в `logs/scanner.log`.
- После завершения всех тестов (`run_all`) в консоль и лог выводится сводка найденных уязвимостей: тип, URL, параметр и использованный payload.

## ⚠️ Дисклеймер

Сканер предназначен **только** для тестирования на специально предоставленных или собственных тестовых стендах (например, локально развёрнутом Juice Shop). Не используйте его против сайтов и систем, на тестирование которых у вас нет явного разрешения.


---

### Что было изменено/добавлено:

1. **Введение** – добавлен абзац, упоминающий модуль SQLi.
2. **Возможности** – добавлен подраздел *SQL Injection* с перечислением проверяемых эндпоинтов и типов уязвимостей.
3. **Стек технологий** – дополнен упоминанием Requests и стандартных библиотек.
4. **Структура проекта** – полностью обновлена: добавлены `models/`, `scanner/sqli_juice_shop.py`, `utils/severity.py`, `utils/sqli_payloads.py`, убраны неиспользуемые файлы (`crawler.py`, `juice_shop_crawler.py`, `text`).
5. **Запуск сканера** – добавлен отдельный подраздел для SQLi с командой запуска и пояснением.
6. **Логи и отчёт** – добавлено упоминание о единой модели `Vulnerability`.
