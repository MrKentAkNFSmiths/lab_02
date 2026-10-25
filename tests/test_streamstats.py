import io
import json
import sys
from pathlib import Path

import pytest
from streamstats.__main__ import main
from streamstats.analysis import LogAnalyzer
from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import LogEvent
from streamstats.parser import parse_csv_stream, parse_jsonl_stream


def test_valid_csv_parsing():
    csv_data = (
        "timestamp,level,source,message\n"
        "2026-10-06T10:00:00+00:00,INFO,api,Service started\n"
        "2026-10-06T10:00:05Z,DEBUG,db,Connected\n"
    )
    file_obj = io.StringIO(csv_data)
    events = list(parse_csv_stream(file_obj))

    assert len(events) == 2
    assert events[0].level == "INFO"
    assert events[0].source == "api"
    assert events[1].level == "DEBUG"
    assert events[1].source == "db"


def test_valid_jsonl_parsing():
    jsonl_data = (
        '{"timestamp": "2026-10-06T10:00:00+00:00", "level": "ERROR", "source": "auth", "message": "Fail"}\n'
        '{"timestamp": "2026-10-06T10:00:05+00:00", "level": "WARNING", "source": "web", "message": "Slow"}\n'
    )
    file_obj = io.StringIO(jsonl_data)
    events = list(parse_jsonl_stream(file_obj))

    assert len(events) == 2
    assert events[0].level == "ERROR"
    assert events[1].level == "WARNING"


def test_empty_file():
    file_obj = io.StringIO("")
    with pytest.raises(InvalidEventError):
        list(parse_csv_stream(file_obj))



def test_invalid_timestamp():
    with pytest.raises(InvalidTimestampError):
        LogEvent.from_raw("не-дата", "INFO", "source", "msg")


def test_invalid_level():
    with pytest.raises(InvalidEventError):
        LogEvent.from_raw("2026-10-06T10:00:00+00:00", "UNKNOWN_LVL", "source", "msg")


def test_empty_source():
    with pytest.raises(InvalidEventError):
        LogEvent.from_raw("2026-10-06T10:00:00+00:00", "INFO", "   ", "msg")


def test_unicode_support():
    event = LogEvent.from_raw(
        "2026-10-06T10:00:00+00:00",
        "INFO",
        "воркер",
        "Задача завершена успешно, пользователь Иван"
    )
    assert event.source == "воркер"
    assert event.message == "Задача завершена успешно, пользователь Иван"


def test_analyzer_aggregation():
    analyzer = LogAnalyzer()
    e1 = LogEvent.from_raw("2026-10-06T10:00:00+00:00", "ERROR", "db", "Error 1")
    e2 = LogEvent.from_raw("2026-10-06T10:05:00+00:00", "INFO", "api", "Info 1")

    analyzer.update(e1)
    analyzer.update(e2)

    data = analyzer.to_dict()
    assert data["total_events"] == 2
    assert data["levels"]["ERROR"] == 1
    assert data["levels"]["INFO"] == 1
    assert data["sources"]["db"] == 1
    assert data["top_error_sources"][0]["source"] == "db"
    assert data["time_range"]["first"] == "2026-10-06T10:00:00+00:00"
    assert data["time_range"]["last"] == "2026-10-06T10:05:00+00:00"


# ==========================================
# 3. ИНТЕГРАЦИОННЫЕ ТЕСТЫ CLI
# ==========================================

class TestCLI:

    def test_cli_success(self, tmp_path: Path, monkeypatch, capsys):
        """Проверка работы CLI при успешном анализе файла."""
        log_file = tmp_path / "logs.jsonl"
        log_file.write_text(
            '{"timestamp": "2026-10-06T10:00:00+00:00", "level": "INFO", "source": "api", "message": "OK"}\n',
            encoding="utf-8",
        )
        report_file = tmp_path / "report.json"

        test_args = [
            "streamstats",
            "analyze",
            str(log_file),
            "--format",
            "jsonl",
            "--output",
            str(report_file),
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        assert report_file.exists()

        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        assert report_data["total_events"] == 1

    def test_cli_invalid_file_error(self, tmp_path: Path, monkeypatch, capsys):
        """Проверка работы CLI при ошибке в файле (вывод в stderr и код выхода 2)."""
        log_file = tmp_path / "bad.jsonl"
        log_file.write_text('{"bad_json": true}\n', encoding="utf-8")
        report_file = tmp_path / "report.json"

        test_args = [
            "streamstats",
            "analyze",
            str(log_file),
            "--format",
            "jsonl",
            "--output",
            str(report_file),
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        captured = capsys.readouterr()
        assert exc_info.value.code in (1, 2)
        assert len(captured.err) > 0

    def test_cli_skip_invalid_mode(self, tmp_path: Path, monkeypatch, capsys):
        """Проверка работы CLI с флагом --skip-invalid при наличии поврежденных строк."""
        log_file = tmp_path / "mixed.jsonl"
        log_file.write_text(
            'invalid_json_line\n'
            '{"timestamp": "2026-10-06T10:00:00+00:00", "level": "INFO", "source": "api", "message": "OK"}\n',
            encoding="utf-8",
        )
        report_file = tmp_path / "report.json"

        test_args = ["streamstats","analyze",str(log_file),"--format","jsonl","--output",str(report_file),"--skip-invalid"]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        assert report_data["total_events"] == 1
        assert report_data["skipped_lines"] == 1

    def test_cli_multiple_files(self, tmp_path: Path, monkeypatch, capsys):
        """Проверка анализа нескольких входных файлов одновременно."""
        f1 = tmp_path / "part1.jsonl"
        f1.write_text(
            '{"timestamp": "2026-10-06T10:00:00+00:00", "level": "INFO", "source": "api", "message": "OK"}\n',
            encoding="utf-8",
        )
        f2 = tmp_path / "part2.jsonl"
        f2.write_text(
            '{"timestamp": "2026-10-06T11:00:00+00:00", "level": "ERROR", "source": "db", "message": "Fail"}\n',
            encoding="utf-8",
        )
        report_file = tmp_path / "report.json"

        test_args = [
            "streamstats",
            "analyze",
            str(f1),
            str(f2),
            "--format",
            "jsonl",
            "--output",
            str(report_file),
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        report_data = json.loads(report_file.read_text(encoding="utf-8"))
        assert report_data["total_events"] == 2
        assert report_data["levels"]["INFO"] == 1
        assert report_data["levels"]["ERROR"] == 1
        assert report_data["time_range"]["first"] == "2026-10-06T10:00:00+00:00"
        assert report_data["time_range"]["last"] == "2026-10-06T11:00:00+00:00"

    def test_cli_file_not_found_error(self, tmp_path: Path, monkeypatch, capsys):
        """Проверка работы CLI при передаче несуществующего файла."""
        test_args = [
            "streamstats",
            "analyze",
            str(tmp_path / "nonexistent.jsonl"),
            "--format",
            "jsonl",
            "--output",
            str(tmp_path / "report.json"),
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        with pytest.raises(SystemExit) as exc_info:
            main()

        captured = capsys.readouterr()
        assert exc_info.value.code in (1, 2)
        assert len(captured.err) > 0