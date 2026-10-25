import csv
import json
from collections.abc import Callable, Iterator
from typing import TextIO

from .errors import InvalidEventError, UnsupportedFormatError
from .models import LogEvent

REQUIRED_FIELDS = {"timestamp", "level", "source", "message"}


def parse_csv_stream(file_obj: TextIO, on_error: Callable[[int, Exception], None] | None = None,) -> Iterator[LogEvent]:
    """Потоковый парсер CSV с заголовком."""
    reader = csv.DictReader(file_obj)
    if not reader.fieldnames or not REQUIRED_FIELDS.issubset(reader.fieldnames):
        raise InvalidEventError(f"CSV файл не содержит обязательных колонок: {REQUIRED_FIELDS}")

    for line_num, row in enumerate(reader, start=2):
        try:
            yield LogEvent.from_raw(
                row.get("timestamp", ""),
                row.get("level", ""),
                row.get("source", ""),
                row.get("message", ""),
            )
        except Exception as e:
            if on_error:
                on_error(line_num, e)
            else:
                raise


def parse_jsonl_stream(file_obj: TextIO,on_error: Callable[[int, Exception], None] | None = None,) -> Iterator[LogEvent]:
    """Потоковый парсер JSONL."""
    for line_num, line in enumerate(file_obj, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as e:
                raise InvalidEventError(f"Ошибка JSON на строке {line_num}: {e.msg}") from e

            if not isinstance(data, dict):
                raise InvalidEventError(f"Строка {line_num} должна быть JSON-объектом")

            if not REQUIRED_FIELDS.issubset(data.keys()):
                missing = REQUIRED_FIELDS - data.keys()
                raise InvalidEventError(
                    f"Строка {line_num} пропустила обязательные поля: {missing}"
                )

            yield LogEvent.from_raw(
                str(data["timestamp"]),
                str(data["level"]),
                str(data["source"]),
                str(data["message"]),
            )
        except Exception as e:
            if on_error:
                on_error(line_num, e)
            else:
                raise


def get_parser(fmt: str):
    """Возвращает потоковый парсер для указанного формата."""
    parsers = {
        "csv": parse_csv_stream,
        "jsonl": parse_jsonl_stream,
    }
    parser = parsers.get(fmt.lower())
    if not parser:
        raise UnsupportedFormatError(
            f"Неподдерживаемый формат: {fmt}. Используйте csv или jsonl"
        )
    return parser