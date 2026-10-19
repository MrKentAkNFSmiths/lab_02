from dataclasses import dataclass
from datetime import datetime
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@dataclass(frozen=True)
class LogEvent:
  timestamp: datetime
  level: LogLevel
  source: str
  message: str

  