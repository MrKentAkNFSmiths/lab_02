import json
from typing import TextIO

from .analysis import LogAnalyzer


def write_report(analyzer: LogAnalyzer, output_file: TextIO) -> None:
    json.dump(analyzer.to_dict(), output_file, ensure_ascii=False, indent=2)