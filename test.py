import requests
import json
from dotenv import load_dotenv
import os

BASE_URL = "example_url"
API_KEY = os.getenv("API_KEY")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "example_model",
    "input": "question",
    "stream": False,
    "temperature": 0.7
}

try:
    response = requests.post(BASE_URL, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()

    print("=" * 50)
    print("질문")
    print("=" * 50)

    if "choices" in result and len(result["choices"]) > 0:
        answer = result["choices"][0]["message"]["content"]
        print(f"답변: {answer}")
    
    else:
        print(f"전체 응답: {json.dumps(result, ensure_ascii=False, indent=2)}")

    print("=" * 50)

except requests.exceptions.HTTPError as e:
    print(f"HTTP 에러 발생: {e}")
