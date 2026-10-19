from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from .errors import InvalidEventError, InvalidTimestampError

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class LogEvent:
  timestamp: datetime
  level: LogLevel
  source: str
  message: str

  def __post_init__(self):
    object.__setattr__(self, "level", self.level.strip().upper())
    if self.level not in VALID_LEVELS:
      raise InvalidEventError(f"Неизвестный уровень лога: '{self.level}'")

    cleaned_source = self.source.strip() if self.source else ""
    if not cleaned_source:
      raise InvalidEventError("Поле 'source' не может быть пустым")
    object.__setattr__(self, "source", cleaned_source)

  @classmethod
  def from_raw(
      cls, timestamp_str: str, level: str, source: str, message: str
  ) -> "LogEvent":
    """Фабричный метод для создания LogEvent из сырых данных."""
    try:
      ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, TypeError) as e:
      raise InvalidTimestampError(
          f"Неверный формат времени ISO 8601: '{timestamp_str}'"
      ) from e

    return cls(
        timestamp=ts,
        level=level,  # type: ignore
        source=source,
        message=message,
    )