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


def strip_json_code_fence(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def build_daily_prompt(filename: str, pdf_text: str) -> str:
    return f"""
당신은 글로벌 정세 분석 전문가입니다.
Eurasia Group의 Daily Brief PDF 원문만을 기반으로 구조화 요약을 작성하세요.

[수신 대상]
- 임원진(C-Level)
- 해당 동향을 바탕으로 담당 고객사(국내 50대 대기업)에 미치는 영향을 판단하는 데 활용

[절대 규칙]
- 입력된 PDF 원문에 명시적으로 기재된 내용만 사용할 것
- AI가 사전 학습한 지식, 외부 정보, 추측, 의견을 절대 포함하지 말 것
- 원문에 없는 수치·사실·인과관계를 임의로 생성하거나 추가하지 말 것
- 확인되지 않는 내용은 쓰지 않는 것이 누락보다 낫다
- 모든 item에는 반드시 출처(PDF파일명 + 원문 문장 그대로 인용)를 포함할 것
- 출처가 없는 item은 작성하지 말 것
- 반드시 markdown 코드블록 없이 순수 JSON만 출력할 것

[처리 목표]
1. 문서 전체를 읽고 국가/지역별 주요 동향을 분류
2. 국내 50대 대기업에 실질적 영향이 있는 이슈를 우선 선별
3. 이후 주간 요약에서 같은 주제를 묶을 수 있도록 topic_key를 안정적으로 생성

[topic_key 작성 규칙]
- 영어 snake_case로 작성
- 같은 주제는 같은 키가 나오도록 최대한 일관되게 작성
- 예: us_tariffs, japan_rate_hike, china_export_controls, middle_east_shipping_risk

[출력 JSON 형식]
{{
  "file_name": "{filename}",
  "document_summary": "문서 전체 3~5줄 요약",
  "items": [
    {{
      "region": "미국",
      "topic_key": "us_tariffs",
      "headline": "해당 주 핵심 내용 한 줄",
      "detail": "세부 내용",
      "implication": "국내 50대 대기업 영향. 없으면 빈 문자열",
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
    response_text = llm_client.summarize_with_images(prompt, image_base64_list=image_b64_list)
    cleaned_text = strip_json_code_fence(response_text)

    try:
        result = json.loads(cleaned_text)
    except json.JSONDecodeError:
        result = {
            "file_name": filename,
            "file_date": file_date,
            "raw_response": response_text,
            "cleaned_response": cleaned_text,
            "items": []
        }

    result["file_date"] = file_date
    result["pdf_path"] = pdf_path

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return output_path