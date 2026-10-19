import csv
import json
from collections.abc import Iterator
from datetime import datetime
from typing import TextIO

from .errors import InvalidEventError, InvalidTimestampError, UnsupportedFormatError
from .models import VALID_LEVELS, LogEvent


def _parse_event(timestamp_str: str, level: str, source: str, message: str) -> LogEvent:

  try:# Проверка таймстампов
    ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
  except (ValueError, TypeError) as e:
    raise InvalidTimestampError(f"Неверный формат времени: {timestamp_str}") from e


  level_upper = level.strip().upper()# Проверка уровня
  if level_upper not in VALID_LEVELS:
    raise InvalidEventError(f"Неизвестный уровень лога: {level}")


  cleaned_source = source.strip()# Проверка источника
  if not cleaned_source:
    raise InvalidEventError("Поле 'source' не может быть пустым")

  return LogEvent(
      timestamp=ts,
      level=level_upper,  # type: ignore
      source=cleaned_source,
      message=message,
  )


def parse_csv_stream(file_obj: TextIO) -> Iterator[LogEvent]:
  """Потоковый парсер CSV с заголовком"""
  reader = csv.DictReader(file_obj)
  required_fields = {"timestamp", "level", "source", "message"}

  if not reader.fieldnames or not required_fields.issubset(reader.fieldnames):
    raise InvalidEventError(
        f"CSV файл не содержит обязательных колонок: {required_fields}"
    )

  for row in reader:
    try:
      yield _parse_event(
          row.get("timestamp", ""),
          row.get("level", ""),
          row.get("source", ""),
          row.get("message", ""),
      )
    except (InvalidEventError, InvalidTimestampError):
      raise
    except Exception as e:
      raise InvalidEventError(f"Ошибка чтения строки CSV: {e}") from e


def parse_jsonl_stream(file_obj) -> Iterator[LogEvent]:
  for line_num, line in enumerate(file_obj, start=1):
    stripped = line.strip()
    if not stripped:
      continue
    try:
      data = json.loads(stripped)
    except json.JSONDecodeError as e:
      raise InvalidEventError(f"Ошибка JSON на строке {line_num}: {e.msg}") from e

    if not isinstance(data, dict):
      raise InvalidEventError(f"Строка {line_num} должна быть JSON-объектом")

    required = {"timestamp", "level", "source", "message"}
    if not required.issubset(data.keys()):
      raise InvalidEventError(
          f"Строка {line_num} пропустила обязательные поля: {required - data.keys()}"
      )

    yield LogEvent.from_raw(
        str(data.get("timestamp", "")),
        str(data.get("level", "")),
        str(data.get("source", "")),
        str(data.get("message", "")),
    )


def get_parser(fmt: str):
  fmt_lower = fmt.lower()
  if fmt_lower == "csv":
    return parse_csv_stream
  elif fmt_lower == "jsonl":
    return parse_jsonl_stream
  else:
    raise UnsupportedFormatError(
        f"Неподдерживаемый формат: {fmt}. Используйте csv или jsonl"
    )