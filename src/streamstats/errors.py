class StreamStatsError(Exception):
  """Базовая ошибка для streamstats."""


class UnsupportedFormatError(StreamStatsError):
  """Неподдерживаемый формат файлов."""


class InvalidEventError(StreamStatsError):
  """Неверное или поврежденное событие."""


class InvalidTimestampError(StreamStatsError):
  """Неверная временная метка (не ISO 8601)."""


class ConfigError(StreamStatsError):
  """Ошибка конфигурации CLI."""