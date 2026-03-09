from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI

from .models import DailySummary


class LLMClient:
    def __init__(self, config: Dict[str, Any]):
        llm_cfg = config["llm"]
        kwargs = {"api_key": llm_cfg["api_key"]}
        if llm_cfg.get("base_url"):
            kwargs["base_url"] = llm_cfg["base_url"]
        self.client = OpenAI(**kwargs)
        self.config = config

    def _chat_completion(self, model: str, messages: List[Dict[str, Any]]) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.config["llm"].get("temperature", 0.1),
            max_tokens=self.config["llm"].get("max_output_tokens", 7000),
        )
        return response.choices[0].message.content or ""

    def summarize_daily_pdf(self, pdf_payload, file_date_iso: str) -> DailySummary:
        system_prompt = self.config["prompt"]["system"]
        user_template = self.config["prompt"]["daily_user_template"]

        content: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    f"{user_template}\n\n"
                    f"file_name: {pdf_payload.file_name}\n"
                    f"file_date: {file_date_iso}\n\n"
                    f"full_text:\n{pdf_payload.full_text[:100000]}"
                ),
            }
        ]

        for page in pdf_payload.pages:
            if page.image_b64:
                content.append(
                    {"type": "text", "text": f"page {page.page_number} text:\n{page.text[:10000]}"}
                )
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{page.image_b64}"},
                    }
                )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

        raw = self._chat_completion(self.config["llm"]["model_vision"], messages)
        data = json.loads(self._extract_json(raw))
        return DailySummary.model_validate(data)

    def build_weekly_report(self, week_start: str, week_end: str, weekly_payload: Dict[str, Any]) -> str:
        system_prompt = self.config["prompt"]["system"]
        user_template = self.config["prompt"]["weekly_user_template"]
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"{user_template}\n\n"
                    f"week_start: {week_start}\n"
                    f"week_end: {week_end}\n\n"
                    f"structured_data:\n{json.dumps(weekly_payload, ensure_ascii=False, indent=2)}"
                ),
            },
        ]
        response = self.client.chat.completions.create(
            model=self.config["llm"]["model_text"],
            messages=messages,
            temperature=self.config["llm"].get("temperature", 0.1),
            max_tokens=self.config["llm"].get("max_output_tokens", 7000),
        )
        return response.choices[0].message.content or ""

    @staticmethod
    def _extract_json(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.replace("```json", "", 1).replace("```", "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Model output does not contain JSON object")
        return raw[start:end + 1]
