import os
import json
import requests
from typing import List, Optional


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model_text: str, model_vision: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.model_text = model_text
        self.model_vision = model_vision or model_text

        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _post(self, payload: dict) -> dict:
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload,
            timeout=180
        )
        response.raise_for_status()
        return response.json()

    def _extract_content(self, result: dict) -> str:
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]

            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]

            if "text" in choice:
                return choice["text"]

        return json.dumps(result, ensure_ascii=False, indent=2)

    def summarize_text(self, prompt: str, temperature: float = 0.2) -> str:
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
        temperature: float = 0.2
    ) -> str:
        """
        네 API가 이미지 입력을 지원하지 않을 수도 있으므로,
        우선 텍스트만 보낼 수 있게 설계.
        이미지 지원 API라면 payload 형식을 네 서버 스펙에 맞게 바꾸면 됨.
        """

        if not image_base64_list:
            return self.summarize_text(prompt, temperature=temperature)

        # 기본값: 이미지 지원이 확실하지 않으므로 텍스트에 이미지 존재 사실만 추가
        image_notice = f"\n\n[참고] 원문에는 이미지/도표 페이지 {len(image_base64_list)}장이 포함되어 있습니다."
        merged_prompt = prompt + image_notice

        payload = {
            "model": self.model_vision,
            "input": merged_prompt,
            "stream": False,
            "temperature": temperature
        }

        result = self._post(payload)
        return self._extract_content(result)