from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional


DATE_PATTERN = re.compile(r"\((\d{1,2})\.(\d{1,2})\)")


def setup_logger(log_dir: str | Path) -> logging.Logger:
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("eg_daily_brief")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(Path(log_dir) / "run.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger


def parse_pdf_date_from_filename(file_name: str, default_year: Optional[int] = None) -> date:
    match = DATE_PATTERN.search(file_name)
    if not match:
        raise ValueError(f"Could not parse date from filename: {file_name}")
    month, day = int(match.group(1)), int(match.group(2))
    year = default_year or datetime.now().year
    return date(year, month, day)


def get_week_start(target: Optional[date] = None) -> date:
    target = target or date.today()
    return target - timedelta(days=target.weekday())


def get_week_end(week_start: date) -> date:
    return week_start + timedelta(days=4)


def normalize_whitespace(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_json(path: str | Path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_pdf_files(directory: str | Path) -> Iterable[Path]:
    return sorted(Path(directory).glob("*.pdf"))
