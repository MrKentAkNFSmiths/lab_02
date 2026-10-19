import json
from typing import TextIO
from .analysis import LogAnalyzer


def write_report(analyzer: LogAnalyzer, output_file: TextIO):
  report_data = analyzer.to_dict()
  output_file.write(json.dumps(report_data, ensure_ascii=False, indent=2))