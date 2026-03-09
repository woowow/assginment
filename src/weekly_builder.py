from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .llm_client import LLMClient
from .models import DailySummary
from .utils import get_week_end, get_week_start, load_json, save_json


class WeeklyBuilder:
    def __init__(self, config: Dict[str, Any], logger):
        self.config = config
        self.logger = logger
        self.llm = LLMClient(config)

    def _load_daily_summaries(self) -> List[DailySummary]:
        daily_dir = Path(self.config["paths"]["daily_json"])
        summaries = []
        for path in sorted(daily_dir.glob("*.json")):
            summaries.append(DailySummary.model_validate(load_json(path)))
        return summaries

    def _filter_week(self, summaries: List[DailySummary], week_start: date) -> List[DailySummary]:
        week_end = get_week_end(week_start)
        selected = []
        for s in summaries:
            d = datetime.fromisoformat(s.file_date).date()
            if week_start <= d <= week_end:
                selected.append(s)
        return selected

    def _collapse_topics(self, summaries: List[DailySummary]) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for summary in summaries:
            for item in summary.items:
                grouped[item.topic_key].append(
                    {
                        "file_date": summary.file_date,
                        "file_name": summary.file_name,
                        "region": item.region,
                        "headline": item.headline,
                        "bullet": item.bullet,
                        "topic_key": item.topic_key,
                        "topic_label": item.topic_label,
                        "impact_hint": item.impact_hint,
                        "source_quotes": [q.model_dump() for q in item.source_quotes],
                    }
                )

        collapsed = []
        for topic_key, items in grouped.items():
            items_sorted = sorted(items, key=lambda x: x["file_date"])
            latest = items_sorted[-1]
            collapsed.append(
                {
                    "topic_key": topic_key,
                    "topic_label": latest["topic_label"],
                    "region": latest["region"],
                    "latest": latest,
                    "history": items_sorted,
                    "trend_summary": self._build_trend_summary(items_sorted),
                }
            )

        collapsed.sort(key=lambda x: (x["region"], x["latest"]["file_date"], x["topic_label"]))
        return {"topics": collapsed}

    @staticmethod
    def _build_trend_summary(items_sorted: List[Dict[str, Any]]) -> str:
        if len(items_sorted) <= 1:
            return ""
        parts = [f"{item['file_date']}: {item['headline']}" for item in items_sorted]
        return " | ".join(parts)

    def build_weekly(self, week_start: Optional[date] = None) -> Dict[str, Any]:
        week_start = week_start or get_week_start()
        week_end = get_week_end(week_start)
        summaries = self._load_daily_summaries()
        weekly_summaries = self._filter_week(summaries, week_start)
        if not weekly_summaries:
            raise ValueError(f"No daily summaries found for week starting {week_start}")

        payload = {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "documents": [s.model_dump() for s in weekly_summaries],
            "collapsed": self._collapse_topics(weekly_summaries),
        }

        report_text = self.llm.build_weekly_report(week_start.isoformat(), week_end.isoformat(), payload)
        payload["weekly_report_markdown"] = report_text

        file_stub = f"weekly_{week_start.isoformat()}"
        output_dir = Path(self.config["paths"]["weekly_reports"])
        json_path = output_dir / f"{file_stub}.json"
        md_path = output_dir / f"{file_stub}.md"
        html_path = output_dir / f"{file_stub}.html"

        save_json(payload, json_path)
        md_path.write_text(report_text, encoding="utf-8")
        html_path.write_text(self.markdown_to_basic_html(report_text), encoding="utf-8")

        self.logger.info("Saved weekly report: %s", md_path)
        return {
            "json_path": str(json_path),
            "md_path": str(md_path),
            "html_path": str(html_path),
            "report_text": report_text,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }

    @staticmethod
    def markdown_to_basic_html(md_text: str) -> str:
        lines = md_text.splitlines()
        html = ["<html><body style='font-family:Malgun Gothic,Arial,sans-serif; line-height:1.6;'>"]
        in_list = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_list:
                    html.append("</ul>")
                    in_list = False
                html.append("<br>")
                continue
            if stripped.startswith("## "):
                if in_list:
                    html.append("</ul>")
                    in_list = False
                html.append(f"<h2>{stripped[3:]}</h2>")
            elif stripped.startswith("**") and stripped.endswith("**"):
                if in_list:
                    html.append("</ul>")
                    in_list = False
                html.append(f"<p><strong>{stripped.strip('*')}</strong></p>")
            elif stripped.startswith("- "):
                if not in_list:
                    html.append("<ul>")
                    in_list = True
                html.append(f"<li>{stripped[2:]}</li>")
            else:
                if in_list:
                    html.append("</ul>")
                    in_list = False
                html.append(f"<p>{stripped}</p>")
        if in_list:
            html.append("</ul>")
        html.append("</body></html>")
        return "\n".join(html)
