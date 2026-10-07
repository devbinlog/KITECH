"""Tests for equipment data parsers."""

from src.parsers import get_parser, CncParser, RobotParser, PlcParser


class TestCncParser:
    """Test CNC machine data parser."""

    def test_parse_running_status(self):
        """CNC parser extracts data and determines RUNNING status."""
        parser = CncParser()
        raw_data = {
            "spindle_rpm": 15000,
            "load_percent": 45.5,
            "temperature": 80.2,
            "alarm_code": "0",
            "program_name": "O1234",
            "feed_rate": 5000,
        }

        parsed, status = parser.parse(raw_data)

        assert status == "RUN"
        assert parsed["spindle_rpm"] == 15000
        assert parsed["load_percent"] == 45.5
        assert parsed["alarm_code"] == "0"

    def test_parse_stopped_status(self):
        """CNC parser returns STOP status when spindle is not running."""
        parser = CncParser()
        raw_data = {
            "spindle_rpm": 0,
            "load_percent": 0,
            "alarm_code": "0",
        }

        parsed, status = parser.parse(raw_data)

        assert status == "STOP"
        assert parsed["spindle_rpm"] == 0

    def test_parse_error_on_alarm(self):
        """CNC parser returns ERROR status when alarm_code is set."""
        parser = CncParser()
        raw_data = {
            "spindle_rpm": 15000,
            "load_percent": 45.5,
            "alarm_code": "E-001",
        }

        parsed, status = parser.parse(raw_data)

        assert status == "ERROR"
        assert parsed["alarm_code"] == "E-001"

    def test_parse_missing_fields(self):
        """CNC parser handles missing fields with defaults."""
        parser = CncParser()
        raw_data = {}

        parsed, status = parser.parse(raw_data)

        assert status == "STOP"
        assert parsed["spindle_rpm"] == 0
        assert parsed["alarm_code"] == "0"


class TestRobotParser:
    """Test Robot data parser."""

    def test_parse_moving_status(self):
        """Robot parser detects moving state correctly."""
        parser = RobotParser()
        raw_data = {
            "joint_angles": [0, 45, 90, -45, 0, 0],
            "battery_level": 85,
            "is_moving": True,
            "error_code": None,
        }

        parsed, status = parser.parse(raw_data)

        assert status == "RUN"
        assert parsed["is_moving"] is True
        assert parsed["battery_level"] == 85

    def test_parse_stopped_status(self):
        """Robot parser returns STOP when not moving."""
        parser = RobotParser()
        raw_data = {
            "joint_angles": [0, 0, 0, 0, 0, 0],
            "battery_level": 90,
            "is_moving": False,
            "error_code": None,
        }

        parsed, status = parser.parse(raw_data)

        assert status == "STOP"
        assert parsed["is_moving"] is False

    def test_parse_error_status(self):
        """Robot parser returns ERROR when error_code is set."""
        parser = RobotParser()
        raw_data = {
            "joint_angles": [0, 0, 0, 0, 0, 0],
            "battery_level": 50,
            "is_moving": False,
            "error_code": "ERR-JOINT",
        }

        parsed, status = parser.parse(raw_data)

        assert status == "ERROR"
        assert parsed["error_code"] == "ERR-JOINT"


class TestPlcParser:
    """Test PLC data parser."""

    def test_parse_running_status(self):
        """PLC parser detects running state."""
        parser = PlcParser()
        raw_data = {
            "registers": {"D0": 100, "D1": 200},
            "coils": {"M0": True},
            "error_flag": False,
            "running": True,
        }

        parsed, status = parser.parse(raw_data)

        assert status == "RUN"
        assert parsed["running"] is True

    def test_parse_error_status(self):
        """PLC parser returns ERROR when error_flag is set."""
        parser = PlcParser()
        raw_data = {
            "error_flag": True,
            "running": True,
        }

        parsed, status = parser.parse(raw_data)

        assert status == "ERROR"


class TestGetParser:
    """Test parser factory function."""

    def test_get_cnc_parser(self):
        """get_parser returns CncParser for CNC type."""
        parser = get_parser("CNC")
        assert isinstance(parser, CncParser)

    def test_get_robot_parser(self):
        """get_parser returns RobotParser for ROBOT type."""
        parser = get_parser("ROBOT")
        assert isinstance(parser, RobotParser)

    def test_get_amr_parser(self):
        """get_parser returns RobotParser for AMR type."""
        parser = get_parser("AMR")
        assert isinstance(parser, RobotParser)

    def test_get_plc_parser(self):
        """get_parser returns PlcParser for PLC type."""
        parser = get_parser("PLC")
        assert isinstance(parser, PlcParser)

    def test_get_unknown_parser(self):
        """get_parser returns CncParser for unknown types."""
        parser = get_parser("UNKNOWN")
        assert isinstance(parser, CncParser)
