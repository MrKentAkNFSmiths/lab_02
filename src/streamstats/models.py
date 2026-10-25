from dataclasses import dataclass
from datetime import datetime

from .errors import InvalidEventError, InvalidTimestampError

VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass
class LogEvent:
    timestamp: datetime
    level: str
    source: str
    message: str

    def __post_init__(self):
        self.level = self.level.strip().upper()
        if self.level not in VALID_LEVELS:
            raise InvalidEventError(f"Неизвестный уровень лога: '{self.level}'")

        self.source = self.source.strip() if self.source else ""
        if not self.source:
            raise InvalidEventError("Поле 'source' не может быть пустым")

    @classmethod
    def from_raw(cls, timestamp_str: str, level: str, source: str, message: str) -> "LogEvent":
        """Создает LogEvent из строковых данных с валидацией."""
        try:
            ts = datetime.fromisoformat(str(timestamp_str).replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise InvalidTimestampError(
                f"Неверный формат времени ISO 8601: '{timestamp_str}'"
            ) from e

        return cls(timestamp=ts, level=level, source=source, message=message)