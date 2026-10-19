import argparse
import sys
import logging
import json
import csv
from pathlib import Path

from .errors import StreamStatsError
from .analysis import LogAnalyzer
from .report import write_report
from .models import LogEvent

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("streamstats")


def main():
    parser = argparse.ArgumentParser(
        description="Потоковый анализатор файлов логов (CSV / JSONL)"
    )
    parser.add_argument(
        "command", choices=["analyze"], help="Команда для выполнения"
    )
    parser.add_argument(
        "inputs", nargs="+", help="Пути к входным файлам (CSV или JSONL)"
    )
    parser.add_argument(
        "--format",
        required=True,
        choices=["csv", "jsonl"],
        help="Формат входных данных",
    )
    parser.add_argument(
        "--output", required=True, help="Путь для сохранения JSON-отчёта"
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Пропускать поврежденные строки с записью WARNING",
    )

    args = parser.parse_args()
    global_analyzer = LogAnalyzer()

    for file_idx, input_path in enumerate(args.inputs, start=1):
        path = Path(input_path)
        if not path.exists():
            print(f"Ошибка: Файл не найден: {input_path}", file=sys.stderr)
            sys.exit(2)

        file_analyzer = LogAnalyzer()

        try:
            with open(path, "r", encoding="utf-8") as f:
                if args.format.lower() == "jsonl":
                    for line_num, line in enumerate(f, start=1):
                        stripped = line.strip()
                        if not stripped:
                            continue
                        try:
                            data = json.loads(stripped)
                            if not isinstance(data, dict):
                                raise StreamStatsError("Строка должна быть JSON-объектом")

                            event = LogEvent.from_raw(
                                str(data.get("timestamp", "")),
                                str(data.get("level", "")),
                                str(data.get("source", "")),
                                str(data.get("message", ""))
                            )
                            file_analyzer.update(event)
                        except (json.JSONDecodeError, StreamStatsError) as e:
                            file_analyzer.skipped_lines += 1
                            if not args.skip_invalid:
                                print(
                                    f"Ошибка в файле '{input_path}' (аргумент #{file_idx}), строка {line_num}: {e}",
                                    file=sys.stderr,
                                )
                                sys.exit(2)
                            else:
                                logger.warning(f"Файл {input_path}, строка {line_num}: пропущено ({e})")

                elif args.format.lower() == "csv":
                    reader = csv.DictReader(f)
                    for line_num, row in enumerate(reader, start=2):  # с учетом заголовка
                        try:
                            event = LogEvent.from_raw(
                                row.get("timestamp", ""),
                                row.get("level", ""),
                                row.get("source", ""),
                                row.get("message", "")
                            )
                            file_analyzer.update(event)
                        except StreamStatsError as e:
                            file_analyzer.skipped_lines += 1
                            if not args.skip_invalid:
                                print(
                                    f"Ошибка в CSV '{input_path}' (аргумент #{file_idx}), строка {line_num}: {e}",
                                    file=sys.stderr,
                                )
                                sys.exit(2)
                            else:
                                logger.warning(f"Файл {input_path}, строка {line_num}: пропущено ({e})")

        except OSError as e:
            print(f"Ошибка чтения файла {input_path}: {e}", file=sys.stderr)
            sys.exit(2)

        global_analyzer.merge(file_analyzer)

    # Сохраняем отчет
    try:
        with open(args.output, "w", encoding="utf-8") as out_f:
            write_report(global_analyzer, out_f)
    except OSError as e:
        print(f"Ошибка записи отчёта: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()