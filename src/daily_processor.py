import os
import re
import json
from datetime import datetime
from typing import Optional

from src.pdf_utils import extract_text_from_pdf, render_pdf_pages_to_base64


DATE_PATTERN = re.compile(r"\((\d{1,2})\.(\d{1,2})\)")


def parse_date_from_filename(filename: str, year: int = 2026) -> Optional[str]:
    match = DATE_PATTERN.search(filename)
    if not match:
        return None

    month = int(match.group(1))
    day = int(match.group(2))
    dt = datetime(year, month, day)
    return dt.strftime("%Y-%m-%d")


def build_daily_prompt(filename: str, pdf_text: str) -> str:
    return f"""
당신은 글로벌 정세 분석 전문가입니다.
아래 Eurasia Group Daily Brief PDF 원문만을 기반으로 구조화 요약을 작성하세요.

[절대 규칙]
- 입력된 원문에 명시적으로 기재된 내용만 사용할 것
- 외부 지식, 추측, 의견을 절대 포함하지 말 것
- 원문에 없는 수치·사실·인과관계를 임의로 생성하지 말 것
- 확인되지 않는 내용은 쓰지 말 것

[해야 할 일]
1. 이 문서의 핵심 이슈를 국가/지역 기준으로 정리
2. 국내 50대 대기업에 영향을 줄 가능성이 있는 사안만 우선 반영
3. 아래 JSON 형식으로만 답변

[출력 JSON 형식]
{{
  "file_name": "{filename}",
  "document_summary": "문서 전체 3~5줄 요약",
  "items": [
    {{
      "region": "미국",
      "topic_key": "us_tariff_policy",
      "headline": "핵심 한 줄",
      "detail": "세부 내용",
      "implication": "국내 기업 영향 또는 빈 문자열",
      "citations": [
        {{
          "quote": "원문 문장 그대로",
          "source": "{filename}"
        }}
      ]
    }}
  ]
}}

[원문]
{pdf_text}
""".strip()


def process_single_pdf(pdf_path: str, llm_client, output_dir: str, year: int = 2026):
    filename = os.path.basename(pdf_path)
    file_date = parse_date_from_filename(filename, year=year)
    pdf_text = extract_text_from_pdf(pdf_path)
    image_b64_list = render_pdf_pages_to_base64(pdf_path, max_pages=3)

    prompt = build_daily_prompt(filename, pdf_text)
    response_text = llm_client.summarize_with_images(prompt, image_b64_list=image_b64_list)

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {
            "file_name": filename,
            "file_date": file_date,
            "raw_response": response_text
        }

    result["file_date"] = file_date
    result["pdf_path"] = pdf_path

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return output_path