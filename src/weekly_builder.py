import os
import json
import html
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


def split_weekly_report_and_references(report_text: str):
    lines = report_text.splitlines()

    main_lines = []
    ref_lines = []

    current_section = None
    last_bullet = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("[주요 아젠다 별 한국 기업에의 영향]"):
            current_section = "agenda"
            main_lines.append(line)
            continue

        if stripped.startswith("[국가 및 권역별 주요 동향 - 상세]"):
            current_section = "regional"
            main_lines.append(line)
            ref_lines.append(line)
            continue

        if stripped.startswith("[출처:"):
            if current_section == "regional":
                if last_bullet:
                    ref_lines.append(last_bullet)
                ref_lines.append(line)
                ref_lines.append("")
            continue

        if current_section == "regional":
            main_lines.append(line)
            if stripped.startswith("- "):
                last_bullet = line
            elif stripped.startswith("**"):
                last_bullet = line
        else:
            main_lines.append(line)

    return "\n".join(main_lines).strip(), "\n".join(ref_lines).strip()

def simple_markdown_to_html(md_text: str, title: str = "Weekly Report") -> str:
    lines = md_text.splitlines()
    html_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            html_lines.append("<div style='height:8px;'></div>")
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            html_lines.append(
                f"<h2 style='margin:20px 0 10px 0; font-size:20px; color:#1f1f1f;'>{html.escape(stripped)}</h2>"
            )
            continue

        if stripped.startswith("**") and stripped.endswith("**"):
            text = stripped.strip("*")
            html_lines.append(
                f"<h3 style='margin:16px 0 8px 0; font-size:17px; color:#2c3e50;'>{html.escape(text)}</h3>"
            )
            continue

        if stripped.startswith("- "):
            text = html.escape(stripped[2:])
            html_lines.append(
                f"<div style='margin:6px 0 6px 18px; line-height:1.6;'>• {text}</div>"
            )
            continue

        if stripped.startswith("(") and stripped.endswith(")"):
            html_lines.append(
                f"<div style='margin:4px 0 8px 22px; color:#555; line-height:1.5;'><i>{html.escape(stripped)}</i></div>"
            )
            continue

        html_lines.append(
            f"<div style='margin:4px 0; line-height:1.6;'>{html.escape(stripped)}</div>"
        )

    body = "\n".join(html_lines)

    return f"""
<html>
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
</head>
<body style="font-family:'Malgun Gothic', Arial, sans-serif; font-size:14px; color:#222; margin:32px; max-width:1000px;">
  <div style="border-bottom:2px solid #e5e7eb; padding-bottom:12px; margin-bottom:20px;">
    <h1 style="margin:0; font-size:24px;">{html.escape(title)}</h1>
  </div>
  {body}
</body>
</html>
""".strip()

def save_weekly_report(weekly_output_dir: str, week_start: str, report_text: str, weekly_input_data: dict):
    os.makedirs(weekly_output_dir, exist_ok=True)

    main_report_text, reference_report_text = split_weekly_report_and_references(report_text)

    md_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}.md")
    html_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}.html")

    ref_md_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}_reference.md")
    ref_html_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}_reference.html")

    json_path = os.path.join(weekly_output_dir, f"weekly_report_{week_start}_input.json")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(main_report_text)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(simple_markdown_to_html(main_report_text, title=f"주간 글로벌 정세 동향 ({week_start})"))

    with open(ref_md_path, "w", encoding="utf-8") as f:
        f.write(reference_report_text)

    with open(ref_html_path, "w", encoding="utf-8") as f:
        f.write(simple_markdown_to_html(reference_report_text, title=f"주간 글로벌 정세 동향 출처 ({week_start})"))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(weekly_input_data, f, ensure_ascii=False, indent=2)

    return md_path, html_path, ref_md_path, ref_html_path, json_path