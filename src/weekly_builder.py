import os
import json
from datetime import datetime, timedelta

from src.prompts import build_weekly_final_prompt


def get_week_range(week_start: str):
    start = datetime.strptime(week_start, "%Y-%m-%d")
    end = start + timedelta(days=4)
    return start.date(), end.date()


def load_daily_jsons(daily_output_dir: str):
    docs = []

    if not os.path.exists(daily_output_dir):
        return docs

    for filename in os.listdir(daily_output_dir):
        if filename.endswith(".json"):
            path = os.path.join(daily_output_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                docs.append(json.load(f))

    return docs


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

    return sorted(filtered, key=lambda x: x.get("file_date", ""))


def select_latest_regional_items(weekly_docs: list):
    latest_by_topic = {}

    for doc in weekly_docs:
        file_date = doc.get("file_date")
        file_name = doc.get("file_name", "")

        for item in doc.get("regional_items", []):
            topic_key = item.get("topic_key")
            if not topic_key:
                continue

            candidate = {
                "file_date": file_date,
                "file_name": file_name,
                "region": item.get("region", ""),
                "headline": item.get("headline", ""),
                "detail": item.get("detail", ""),
                "implication": item.get("implication", ""),
                "citations": item.get("citations", []),
                "topic_key": topic_key
            }

            existing = latest_by_topic.get(topic_key)
            if existing is None or file_date > existing["file_date"]:
                latest_by_topic[topic_key] = candidate

    return latest_by_topic


def build_weekly_input_data(weekly_docs: list, latest_items: dict):
    start_date = weekly_docs[0]["file_date"] if weekly_docs else ""
    end_date = weekly_docs[-1]["file_date"] if weekly_docs else ""

    return {
        "week_files": [
            {
                "file_name": doc.get("file_name"),
                "file_date": doc.get("file_date"),
                "daily_two_line_summary": doc.get("daily_two_line_summary", []),
                "document_summary": doc.get("document_summary", "")
            }
            for doc in weekly_docs
        ],
        "latest_regional_items": list(latest_items.values()),
        "notes": {
            "rule": "같은 topic_key가 여러 번 등장하면 가장 최신 file_date의 항목을 우선 사용"
        },
        "period_actual_start": start_date,
        "period_actual_end": end_date
    }


def build_weekly_report_text(llm_client, week_start: str, weekly_docs: list):
    if not weekly_docs:
        raise ValueError("해당 주차에 사용할 일간 JSON 파일이 없습니다.")

    _, week_end_date = get_week_range(week_start)
    week_end = week_end_date.strftime("%Y-%m-%d")

    latest_items = select_latest_regional_items(weekly_docs)
    weekly_input_data = build_weekly_input_data(weekly_docs, latest_items)

    prompt = build_weekly_final_prompt(week_start, week_end, weekly_input_data)
    weekly_text = llm_client.summarize_text(prompt, temperature=0.0)

    return weekly_text, weekly_input_data


def save_weekly_report(weekly_output_dir: str, week_start: str, report_text: str, weekly_input_data: dict) -> tuple[str, str]:
    os.makedirs(weekly_output_dir, exist_ok=True)

    md_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}.md")
    json_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}_input.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(weekly_input_data, f, ensure_ascii=False, indent=2)

    return md_path, json_path