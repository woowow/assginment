from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

from src.config import ensure_directories, load_config
from src.daily_processor import DailyProcessor
from src.outlook_sender import OutlookSender
from src.weekly_builder import WeeklyBuilder
from src.utils import get_week_start, setup_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EG Daily Brief automation")
    parser.add_argument("command", choices=["process-daily", "build-weekly", "send-weekly"])
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--week", default=None, help="Week start date in YYYY-MM-DD")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def resolve_week_start(week_str: str | None) -> date:
    if week_str:
        return datetime.strptime(week_str, "%Y-%m-%d").date()
    return get_week_start()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    ensure_directories(config)
    logger = setup_logger(config["paths"]["logs"])

    if args.command == "process-daily":
        processor = DailyProcessor(config, logger)
        processed = processor.process_all(force=args.force)
        logger.info("Processed %s PDFs", len(processed))
        return

    week_start = resolve_week_start(args.week)
    builder = WeeklyBuilder(config, logger)

    if args.command == "build-weekly":
        result = builder.build_weekly(week_start)
        logger.info("Weekly report built: %s", result["md_path"])
        return

    if args.command == "send-weekly":
        result = builder.build_weekly(week_start)
        html_body = Path(result["html_path"]).read_text(encoding="utf-8")
        subject_template = config["app"]["executive_email_subject"]
        range_text = f"{result['week_start']} ~ {result['week_end']}"
        subject = subject_template.format(range=range_text)
        sender = OutlookSender(config, logger)
        sender.send_html_report(subject, html_body)
        return


if __name__ == "__main__":
    main()
