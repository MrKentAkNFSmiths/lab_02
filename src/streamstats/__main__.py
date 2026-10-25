import argparse
import logging
import sys
from pathlib import Path

from .analysis import LogAnalyzer
from .errors import StreamStatsError
from .parser import get_parser
from .report import write_report

logging.basicConfig(format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Потоковый анализатор файлов логов (CSV / JSONL)")
    parser.add_argument("command", choices=["analyze"], help="Команда для выполнения")
    parser.add_argument("inputs", nargs="+", help="Пути к входным файлам (CSV или JSONL)")
    parser.add_argument("--format", required=True, choices=["csv", "jsonl"], help="Формат входных данных")
    parser.add_argument("--output", required=True, help="Путь для сохранения JSON-отчёта")
    parser.add_argument("--skip-invalid", action="store_true", help="Пропускать поврежденные строки с записью WARNING")
    return parser



def main():
    args = build_parser().parse_args()

    try:
        parser_func = get_parser(args.format)
    except StreamStatsError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(2)

    analyzer = LogAnalyzer()

    for input_path in args.inputs:
        path = Path(input_path)
        if not path.is_file():
            print(f"Ошибка: Файл не найден: {input_path}", file=sys.stderr)
            sys.exit(2)

        def on_error(line_num: int, err: Exception, current_path: str = input_path):
            analyzer.skipped_lines += 1
            logger.warning(f"Файл {current_path}, строка {line_num}: пропущено ({err})")



        try:
            with open(path, "r", encoding="utf-8") as f:
                for event in parser_func(f, on_error=on_error if args.skip_invalid else None):
                    analyzer.update(event)
        except StreamStatsError as e:
            print(f"Ошибка в файле '{input_path}': {e}", file=sys.stderr)
            sys.exit(2)
        except OSError as e:
            print(f"Ошибка чтения файла {input_path}: {e}", file=sys.stderr)
            sys.exit(2)

    try:
        with open(args.output, "w", encoding="utf-8") as out_f:
            write_report(analyzer, out_f)
    except OSError as e:
        print(f"Ошибка записи отчёта: {e}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()