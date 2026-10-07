from datetime import datetime, time
from zoneinfo import ZoneInfo

from mes_interface_sync.main import next_scheduled_run


def test_next_scheduled_run_returns_later_time_today() -> None:
    timezone = ZoneInfo("Asia/Seoul")
    now = datetime(2026, 9, 7, 1, 30, tzinfo=timezone)

    next_run = next_scheduled_run(now, (time(2, 0), time(14, 0)), timezone)

    assert next_run == datetime(2026, 9, 7, 2, 0, tzinfo=timezone)


def test_next_scheduled_run_rolls_over_to_next_day() -> None:
    timezone = ZoneInfo("Asia/Seoul")
    now = datetime(2026, 9, 7, 14, 30, tzinfo=timezone)

    next_run = next_scheduled_run(now, (time(2, 0), time(14, 0)), timezone)

    assert next_run == datetime(2026, 9, 8, 2, 0, tzinfo=timezone)
