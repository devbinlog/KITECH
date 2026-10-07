"""Tests for LOG file parser."""

import pytest
from pathlib import Path
from datetime import datetime

from src.parsers.log_parser import LogParser
from src.models.monitoring_data import MonitoringRecord

# Sample data path
SAMPLES_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "samples"
    / "digital-thread-project-manager"
    / "tdms"
)


class TestLogParser:
    """Test cases for LogParser."""

    @pytest.fixture
    def sample_log_path(self) -> Path:
        """Get path to sample LOG file."""
        return SAMPLES_DIR / "sample.log"

    @pytest.fixture
    def parser(self, sample_log_path: Path) -> LogParser:
        """Create parser instance."""
        if not sample_log_path.exists():
            pytest.skip(f"Sample file not found: {sample_log_path}")
        return LogParser(sample_log_path)

    def test_get_headers(self, parser: LogParser):
        """Test header extraction."""
        headers = parser.get_headers()

        assert len(headers) > 0
        assert "time" in headers
        assert "crpm" in headers
        assert "cfr" in headers
        assert "cpx" in headers
        assert "cpy" in headers
        assert "cpz" in headers

    def test_get_record_count(self, parser: LogParser):
        """Test record count."""
        count = parser.get_record_count()

        assert count > 0
        print(f"Record count: {count}")

    def test_get_time_range(self, parser: LogParser):
        """Test time range extraction."""
        start_time, end_time = parser.get_time_range()

        assert isinstance(start_time, datetime)
        assert isinstance(end_time, datetime)
        assert end_time >= start_time

        duration = (end_time - start_time).total_seconds()
        print(f"Time range: {start_time} to {end_time} ({duration:.1f}s)")

    def test_parse_records(self, parser: LogParser):
        """Test parsing records."""
        records = list(parser.parse())

        assert len(records) > 0

        # Check first record
        first = records[0]
        assert isinstance(first, MonitoringRecord)
        assert isinstance(first.timestamp, datetime)
        assert isinstance(first.spindle_rpm, float)
        assert isinstance(first.feedrate, float)
        assert isinstance(first.position, tuple)
        assert len(first.position) == 3

        print(f"First record: {first}")
        print(f"Last record: {records[-1]}")

    def test_parse_values(self, parser: LogParser):
        """Test that parsed values are reasonable."""
        records = list(parser.parse())

        # Check that we have cutting and non-cutting records
        cutting_count = sum(1 for r in records if r.cutting)
        non_cutting_count = len(records) - cutting_count

        print(f"Cutting: {cutting_count}, Non-cutting: {non_cutting_count}")

        # Check RPM values are in reasonable range
        max_rpm = max(r.spindle_rpm for r in records)
        min_rpm = min(r.spindle_rpm for r in records)

        assert max_rpm < 50000, "RPM seems too high"
        assert min_rpm >= 0, "RPM should not be negative"

        print(f"RPM range: {min_rpm:.0f} - {max_rpm:.0f}")

    def test_get_file_info(self, parser: LogParser):
        """Test file info retrieval."""
        info = parser.get_file_info()

        assert "path" in info
        assert "format" in info
        assert info["format"] == "LOG"
        assert "record_count" in info
        assert "start_time" in info
        assert "end_time" in info
        assert "duration_seconds" in info

        print(f"File info: {info}")


class TestLogParserTimestamp:
    """Test timestamp parsing."""

    def test_parse_timestamp_format(self):
        """Test various timestamp formats."""
        parser = LogParser.__new__(LogParser)

        # Standard format: YYMMDD HH:MM:SS.mmm
        ts = parser._parse_timestamp("250112 11:18:11.450")
        assert ts.year == 2025
        assert ts.month == 1
        assert ts.day == 12
        assert ts.hour == 11
        assert ts.minute == 18
        assert ts.second == 11
        assert ts.microsecond == 450000

    def test_parse_timestamp_edge_cases(self):
        """Test edge cases in timestamp parsing."""
        parser = LogParser.__new__(LogParser)

        # Without milliseconds
        ts = parser._parse_timestamp("250112 11:18:11")
        assert ts.hour == 11

        # Invalid format should return current time (not crash)
        ts = parser._parse_timestamp("invalid")
        assert isinstance(ts, datetime)
