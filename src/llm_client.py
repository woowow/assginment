import json
import requests
from typing import List, Optional


class LLMClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_text: str,
        model_vision: Optional[str] = None,
        timeout_seconds: int = 300,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model_text = model_text
        self.model_vision = model_vision or model_text
        self.timeout_seconds = timeout_seconds

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _post(self, payload: dict) -> dict:
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload,
            timeout=self.timeout_seconds
        )
        response.raise_for_status()
        return response.json()

    def _extract_content(self, result: dict) -> str:
        if "output" in result and isinstance(result["output"], list):
            for output_item in result["output"]:
                if output_item.get("type") == "message":
                    for content_item in output_item.get("content", []):
                        if content_item.get("type") == "output_text":
                            return content_item.get("text", "")

        if "choices" in result and isinstance(result["choices"], list) and result["choices"]:
            choice = result["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            if "text" in choice:
                return choice["text"]

        return json.dumps(result, ensure_ascii=False, indent=2)

    def summarize_text(self, prompt: str, temperature: float = 0.0) -> str:
        payload = {
            "model": self.model_text,
            "input": prompt,
            "stream": False,
            "temperature": temperature
        }
        result = self._post(payload)
        return self._extract_content(result)

    def summarize_with_images(
        self,
        prompt: str,
        image_base64_list: Optional[List[str]] = None,
        temperature: float = 0.0
    ) -> str:
        # 현재 API 이미지 스펙 미확인 상태라 텍스트 기반으로 우선 처리
        if image_base64_list:
            prompt += (
                f"\n\n[참고] 원문 PDF에는 이미지/도표가 포함되어 있으며 "
                f"앞부분 기준 {len(image_base64_list)}장의 시각 자료가 존재합니다. "
                f"텍스트에 명시된 내용만 사용하고 추측은 금지합니다."
            )
        return self.summarize_text(prompt, temperature=temperature)