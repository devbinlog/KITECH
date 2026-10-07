from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .config import Settings
from .sync_service import MesInterfaceSyncService

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def next_scheduled_run(now: datetime, schedule: tuple[time, ...], timezone: ZoneInfo) -> datetime:
    today = now.astimezone(timezone).date()
    for scheduled_time in schedule:
        candidate = datetime.combine(today, scheduled_time, tzinfo=timezone)
        if candidate > now:
            return candidate
    return datetime.combine(today + timedelta(days=1), schedule[0], tzinfo=timezone)


async def run_forever(settings: Settings) -> None:
    service = MesInterfaceSyncService(settings)
    timezone = ZoneInfo(settings.sync_timezone)

    if settings.sync_run_on_start:
        batch_id = await service.run_once()
        logger.info("startup sync completed batch_id=%s", batch_id)

    while True:
        now = datetime.now(timezone)
        next_run = next_scheduled_run(now, settings.sync_schedule, timezone)
        sleep_seconds = max(0.0, (next_run - now).total_seconds())
        logger.info(
            "next MES interface sync scheduled_at=%s timezone=%s",
            next_run.isoformat(timespec="minutes"),
            settings.sync_timezone,
        )
        await asyncio.sleep(sleep_seconds)
        batch_id = await service.run_once()
        logger.info("scheduled sync completed batch_id=%s", batch_id)


async def run_sync_once(settings: Settings) -> None:
    service = MesInterfaceSyncService(settings)
    batch_id = await service.run_once()
    logging.getLogger(__name__).info("sync-once completed batch_id=%s", batch_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MES SQLite to PostgreSQL Interface DB sync worker")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("run", "sync-once"),
        default="run",
        help="run continuously or execute a single sync batch",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    if args.command == "sync-once":
        asyncio.run(run_sync_once(settings))
    else:
        asyncio.run(run_forever(settings))


if __name__ == "__main__":
    main()
