import os
import re
import json
from datetime import datetime
from typing import Optional

from src.pdf_utils import extract_text_from_pdf, render_pdf_pages_to_base64
from src.prompts import build_daily_short_prompt, build_daily_structured_prompt


DATE_PATTERN = re.compile(r"\((\d{1,2})\.(\d{1,2})\)")


def parse_date_from_filename(filename: str, year: int = 2026) -> Optional[str]:
    match = DATE_PATTERN.search(filename)
    if not match:
        return None

    month = int(match.group(1))
    day = int(match.group(2))
    dt = datetime(year, month, day)
    return dt.strftime("%Y-%m-%d")


def strip_json_code_fence(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def safe_load_json(text: str) -> dict:
    cleaned = strip_json_code_fence(text)
    return json.loads(cleaned)


def process_single_pdf(pdf_path: str, llm_client, output_dir: str, year: int = 2026):
    filename = os.path.basename(pdf_path)
    file_date = parse_date_from_filename(filename, year=year)
    pdf_text = extract_text_from_pdf(pdf_path)
    image_b64_list = render_pdf_pages_to_base64(pdf_path, max_pages=2)

    short_prompt = build_daily_short_prompt(filename, pdf_text)
    structured_prompt = build_daily_structured_prompt(filename, pdf_text)

    short_response = llm_client.summarize_with_images(short_prompt, image_base64_list=image_b64_list)
    structured_response = llm_client.summarize_with_images(structured_prompt, image_base64_list=image_b64_list)

    result = {
        "file_name": filename,
        "file_date": file_date,
        "pdf_path": pdf_path,
        "daily_two_line_summary": [],
        "document_summary": "",
        "regional_items": [],
    }

    try:
        short_json = safe_load_json(short_response)
        result["daily_two_line_summary"] = short_json.get("daily_two_line_summary", [])
    except Exception:
        result["daily_short_raw_response"] = short_response

    try:
        structured_json = safe_load_json(structured_response)
        result["document_summary"] = structured_json.get("document_summary", "")
        result["regional_items"] = structured_json.get("regional_items", [])
    except Exception:
        result["daily_structured_raw_response"] = structured_response

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return output_path