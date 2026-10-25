# Потоковый анализатор логов (streamstats)
___
 Консольная программа для потокового анализа и сбора статистики по лог-файлам в форматах CSV и JSONL без полной загрузки в оперативную память
___
## Функции

>- Потоковое чтение: обработка файлов построчно с минимальным потреблением памяти.
>- Поддержка форматов: CSV (с заголовком) и JSONL.
>- Валидация событий: проверка обязательных полей (`timestamp`, `level`, `source`, `message`), уровней логирования и формата ISO 8601.
>- Подсчет статистики: подсчет общего числа событий, распределения по уровням и источникам, поиск top-5 источников ошибок и диапазона временных меток.
>- Режимы работы с ошибками: строгий (выход с кодом `2`) и с флагом `--skip-invalid` (пропуск поврежденных строк с логированием).


## Установка

```bash
python3 -m venv venv
source venv/bin/activate 
pip3 install -e ".[dev]"
```

## Команды

### Проверка

```bash
python -m pytest
ruff check .
python -m streamstats --help
```

### Анализ логов

```bash
python3 -m streamstats analyze logs.jsonl --format jsonl --output report.json
# Создает JSON-отчет "report.json" по результатам анализа файла "logs.jsonl"
```

### Анализ нескольких файлов с пропуском ошибок

```bash
python3 -m streamstats analyze file1.csv file2.csv --format csv --output report.json --skip-invalid
# Объединяет статистику и пропускает поврежденные строки
```

### Help
```bash
python3 -m streamstats --help 
# Выведется справка по использованию CLI
```

## Структура
```
lab_02/
├── src/
│   └── streamstats/
│       ├── __init__.py
│       ├── __main__.py     # Точка входа CLI и оркестрация 
│       ├── models.py       # Модель события и валидация
│       ├── parser.py       # Потоковые парсеры CSV и JSONL
│       ├── analysis.py     # Логика сбора статистики
│       ├── report.py       # Генерация JSON-отчёта
│       └── errors.py       # Кастомные исключения
├── tests/
│   └── test_streamstats.py # Набор юнит-тестов pytest
├── pyproject.toml          # Конфигурация проекта
└── README.md
```
