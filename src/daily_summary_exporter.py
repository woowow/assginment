import csv
import os


def append_daily_summary_csv(csv_path: str, result: dict):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    file_exists = os.path.exists(csv_path)

    row = {
        "file_date": result.get("file_date", ""),
        "file_name": result.get("file_name", ""),
        "daily_summary_1": "",
        "daily_summary_2": "",
        "document_summary": result.get("document_summary", ""),
        "regions": "",
        "topic_keys": "",
    }

    daily_lines = result.get("daily_two_line_summary", [])
    if len(daily_lines) > 0:
        row["daily_summary_1"] = daily_lines[0]
    if len(daily_lines) > 1:
        row["daily_summary_2"] = daily_lines[1]

    regional_items = result.get("regional_items", [])
    row["regions"] = ", ".join(
        sorted({item.get("region", "") for item in regional_items if item.get("region")})
    )
    row["topic_keys"] = ", ".join(
        sorted({item.get("topic_key", "") for item in regional_items if item.get("topic_key")})
    )

    fieldnames = [
        "file_date",
        "file_name",
        "daily_summary_1",
        "daily_summary_2",
        "document_summary",
        "regions",
        "topic_keys",
    ]

    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)