import argparse
import sys
import logging
from pathlib import Path

from .errors import StreamStatsError
from .parser import get_parser
from .analysis import LogAnalyzer
from .report import write_report

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("streamstats")


def main():
    parser = argparse.ArgumentParser(
        description="Потоковый анализатор файлов логов (CSV/JSONL)"
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

    parser_func = get_parser(args.format)
    global_analyzer = LogAnalyzer()

    for file_idx, input_path in enumerate(args.inputs, start=1):
        path = Path(input_path)
        if not path.exists():
            print(f"Ошибка: Файл не найден: {input_path}", file=sys.stderr)
            sys.exit(2)

        file_analyzer = LogAnalyzer()
        try:
            with open(path, "r", encoding="utf-8") as f:
                stream = parser_func(f)
                line_num = 0
                for event in stream:
                    line_num += 1
                    file_analyzer.update(event)
        except StreamStatsError as e:
            if not args.skip_invalid:
                print(
                    f"Ошибка в файле '{input_path}' (номер аргумента: {file_idx}), около строки {line_num + 1}: {e}",
                    file=sys.stderr,
                )
                sys.exit(2)
            else:
                file_analyzer.skipped_lines += 1
                logger.warning(
                    f"Файл {input_path}, строка {line_num + 1}: пропущено ({e})"
                )

        global_analyzer.merge(file_analyzer)

    try:
        with open(args.output, "w", encoding="utf-8") as out_f:
            write_report(global_analyzer, out_f)
    except Exception as e:
        print(f"Ошибка записи отчёта: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()