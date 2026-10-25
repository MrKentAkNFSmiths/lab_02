from collections import Counter

from .models import LogEvent


class LogAnalyzer:
    def __init__(self):
        self.total_events = 0
        self.levels_count: Counter[str] = Counter()
        self.sources_count: Counter[str] = Counter()
        self.error_sources_count: Counter[str] = Counter()
        self.min_timestamp: str | None = None
        self.max_timestamp: str | None = None
        self.skipped_lines = 0

    def update(self, event: LogEvent):
        self.total_events += 1
        self.levels_count[event.level] += 1
        self.sources_count[event.source] += 1

        if event.level in {"ERROR", "CRITICAL"}:
            self.error_sources_count[event.source] += 1

        ts_iso = event.timestamp.isoformat()
        if self.min_timestamp is None or ts_iso < self.min_timestamp:
            self.min_timestamp = ts_iso
        if self.max_timestamp is None or ts_iso > self.max_timestamp:
            self.max_timestamp = ts_iso


    def to_dict(self) -> dict:
        top_errors = [
            {"source": src, "count": cnt}
            for src, cnt in self.error_sources_count.most_common(5)
        ]
        return {
            "total_events": self.total_events,
            "levels": dict(self.levels_count),
            "sources": dict(self.sources_count),
            "top_error_sources": top_errors,
            "time_range": {
                "first": self.min_timestamp,
                "last": self.max_timestamp,
            },
            "skipped_lines": self.skipped_lines,
        }