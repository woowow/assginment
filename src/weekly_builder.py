import os
import json
from datetime import datetime, timedelta


def get_week_range(week_start: str):
    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=4)
    return start.date(), end.date()


def load_daily_jsons(daily_output_dir: str):
    items = []
    for filename in os.listdir(daily_output_dir):
        if filename.endswith(".json"):
            path = os.path.join(daily_output_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                items.append(json.load(f))
    return items


def filter_weekly_docs(docs: list, week_start: str):
    start_date, end_date = get_week_range(week_start)
    filtered = []

    for doc in docs:
        file_date = doc.get("file_date")
        if not file_date:
            continue

        dt = datetime.strptime(file_date, "%Y-%m-%d").date()
        if start_date <= dt <= end_date:
            filtered.append(doc)

    return filtered


def select_latest_items(weekly_docs: list):
    latest_by_topic = {}

    for doc in weekly_docs:
        file_date = doc.get("file_date")
        for item in doc.get("items", []):
            topic_key = item.get("topic_key")
            if not topic_key:
                continue

            current = latest_by_topic.get(topic_key)
            if current is None or file_date > current["file_date"]:
                latest_by_topic[topic_key] = {
                    "file_date": file_date,
                    "item": item,
                    "source_file": doc.get("file_name")
                }

    return latest_by_topic


def build_weekly_markdown(week_start: str, latest_items: dict) -> str:
    sorted_items = sorted(
        latest_items.values(),
        key=lambda x: (x["item"].get("region", ""), x["item"].get("headline", ""))
    )

    lines = []
    lines.append(f"## 주간 글로벌 정세 동향 ({week_start}~)")
    lines.append("")

    current_region = None
    for entry in sorted_items:
        item = entry["item"]
        region = item.get("region", "기타")

        if region != current_region:
            lines.append(f"**{region}**")
            lines.append("")
            current_region = region

        headline = item.get("headline", "")
        detail = item.get("detail", "")
        implication = item.get("implication", "")
        citations = item.get("citations", [])

        line = f"- {headline}: {detail}"
        if implication:
            line += f" -> {implication}"
        lines.append(line)

        for c in citations:
            quote = c.get("quote", "")
            source = c.get("source", "")
            lines.append(f'  [출처: {source} | 원문: "{quote}"]')

        lines.append("")

    return "\n".join(lines)


def save_weekly_report(weekly_output_dir: str, week_start: str, markdown_text: str) -> str:
    os.makedirs(weekly_output_dir, exist_ok=True)
    output_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    return output_path