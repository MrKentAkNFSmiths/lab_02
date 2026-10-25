class StreamStatsError(Exception):
    """Базовая ошибка для streamstats."""


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат файлов."""


class InvalidEventError(StreamStatsError):
    """Неверное или поврежденное событие."""


class InvalidTimestampError(StreamStatsError):
    """Неверная временная метка (не ISO 8601)."""


class CSVParseError(InvalidEventError):
    """Ошибка при парсинге CSV файла."""


class JSONLParseError(InvalidEventError):
    """Ошибка при парсинге JSONL файла."""