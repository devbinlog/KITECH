"""Tests for TDMS file parser."""

import pytest
from pathlib import Path
from datetime import datetime

from src.parsers.tdms_parser import TDMSParser
from src.models.monitoring_data import MonitoringRecord

# Sample data path
SAMPLES_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "samples"
    / "digital-thread-project-manager"
    / "tdms"
)


class TestTDMSParser:
    """Test cases for TDMSParser."""

    @pytest.fixture
    def sample_tdms_path(self) -> Path:
        """Get path to sample TDMS file."""
        return SAMPLES_DIR / "sample.tdms"

    @pytest.fixture
    def parser(self, sample_tdms_path: Path) -> TDMSParser:
        """Create parser instance."""
        if not sample_tdms_path.exists():
            pytest.skip(f"Sample file not found: {sample_tdms_path}")
        return TDMSParser(sample_tdms_path)

    def test_get_channels(self, parser: TDMSParser):
        """Test channel listing."""
        channels = parser.get_channels()

        assert len(channels) > 0
        print(f"Channels ({len(channels)}): {channels[:10]}...")

        # Check for expected channel patterns in TDMS format
        # TDMS uses "Group/Channel" format with different naming convention
        channel_str = " ".join(channels).lower()
        assert "position" in channel_str or "cnc" in channel_str, "Missing position or CNC channels"

    def test_get_record_count(self, parser: TDMSParser):
        """Test record count."""
        count = parser.get_record_count()

        assert count > 0
        print(f"Record count: {count}")

    def test_parse_records(self, parser: TDMSParser):
        """Test parsing records."""
        # Only parse first 100 records for speed
        records = []
        for i, record in enumerate(parser.parse()):
            records.append(record)
            if i >= 99:
                break

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
        print(f"Record 100: {records[-1]}")

    def test_parsed_values_reasonable(self, parser: TDMSParser):
        """Test that parsed values are reasonable."""
        records = list(parser.parse())[:100]

        assert len(records) > 0

        # Check position values are in reasonable range
        for r in records:
            assert -10000 < r.position[0] < 10000, f"X position out of range: {r.position[0]}"
            assert -10000 < r.position[1] < 10000, f"Y position out of range: {r.position[1]}"
            assert -10000 < r.position[2] < 10000, f"Z position out of range: {r.position[2]}"

        # Check that we have some variation in positions
        x_positions = [r.position[0] for r in records]
        y_positions = [r.position[1] for r in records]
        z_positions = [r.position[2] for r in records]

        print(f"X range: {min(x_positions):.2f} - {max(x_positions):.2f}")
        print(f"Y range: {min(y_positions):.2f} - {max(y_positions):.2f}")
        print(f"Z range: {min(z_positions):.2f} - {max(z_positions):.2f}")

    def test_get_file_info(self, parser: TDMSParser):
        """Test file info retrieval (may be slow for large files)."""
        info = parser.get_file_info()

        assert "path" in info
        assert "format" in info
        assert info["format"] == "TDMS"
        assert "channels" in info
        assert "record_count" in info

        print(f"File info: path={info['path']}, records={info['record_count']}")
        print(f"Duration: {info.get('duration_seconds', 0):.1f}s")


class TestTDMSParserSmallSample:
    """Test with smaller operations for CI."""

    @pytest.fixture
    def sample_tdms_path(self) -> Path:
        """Get path to sample TDMS file."""
        return SAMPLES_DIR / "sample.tdms"

    def test_file_can_be_opened(self, sample_tdms_path: Path):
        """Test that TDMS file can be opened."""
        if not sample_tdms_path.exists():
            pytest.skip(f"Sample file not found: {sample_tdms_path}")

        parser = TDMSParser(sample_tdms_path)
        channels = parser.get_channels()

        assert len(channels) > 0

    def test_parse_first_records(self, sample_tdms_path: Path):
        """Test parsing first few records."""
        if not sample_tdms_path.exists():
            pytest.skip(f"Sample file not found: {sample_tdms_path}")

        parser = TDMSParser(sample_tdms_path)

        count = 0
        for record in parser.parse():
            assert isinstance(record, MonitoringRecord)
            count += 1
            if count >= 10:
                break

        assert count == 10

    def test_timestamp_parsing(self, sample_tdms_path: Path):
        """Test that timestamps are parsed correctly."""
        if not sample_tdms_path.exists():
            pytest.skip(f"Sample file not found: {sample_tdms_path}")

        parser = TDMSParser(sample_tdms_path)

        records = list(parser.parse())[:10]

        # All timestamps should be valid datetimes
        for r in records:
            assert isinstance(r.timestamp, datetime)
            # Timestamps should be within reasonable range (year 2000-2100)
            assert 2000 <= r.timestamp.year <= 2100

        # Timestamps should be non-decreasing
        for i in range(1, len(records)):
            assert records[i].timestamp >= records[i - 1].timestamp
