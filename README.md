# EG Daily Brief 자동화 프로토타입

이 프로젝트는 `(M.DD) EG Daily Brief_제목.pdf` 형식의 PDF를 읽어,

1. 일간 요약 JSON 저장
2. 주간 요약 HTML/Markdown 생성
3. Microsoft Outlook으로 간부진 메일 발송

까지 자동화하는 Python 기반 MVP입니다.

## 핵심 기능
- PDF 파일명에서 날짜 추출
- PDF 텍스트 추출 + 페이지 이미지 렌더링
- LLM으로 문서 구조화 요약(JSON) 생성
- 주제별 중복 제거 및 최신본 우선 반영
- 금요일 13시 기준 주간 보고서 생성/발송
- 설정 파일만 수정하면 시간/수신자/경로 변경 가능

## 폴더 구조
- `input_pdfs/`: Daily Brief PDF 저장 폴더
- `daily_json/`: PDF별 구조화 요약 결과
- `weekly_reports/`: 주간 보고서 HTML/MD
- `logs/`: 실행 로그
- `src/`: 소스 코드

## 빠른 시작
```bash
pip install -r requirements.txt
copy config.example.yaml config.yaml
```

`config.yaml`을 수정한 뒤:

```bash
python main.py process-daily
python main.py build-weekly --week 2026-03-02
python main.py send-weekly --week 2026-03-02
```

## Windows 작업 스케줄러 권장 실행
금요일 13:00 자동 발송 예시:

작업 시작 프로그램:
- Program/script: `python`
- Add arguments: `main.py send-weekly`
- Start in: 프로젝트 루트 경로

일간 처리 예시:
- 평일 오전 8시 / 오후 5시 등 원하는 시간에 `python main.py process-daily`

## LLM 가정
이 코드는 OpenAI 호환 API를 사용하도록 작성되어 있습니다.
- `api_key`
- `base_url` (필요 시)
- `model_text`
- `model_vision`

를 `config.yaml`에서 설정하세요.

## Outlook 가정
- Windows 환경
- Microsoft Outlook 데스크톱 설치
- 해당 계정에서 메일 발송 가능

## 권장 운영 순서
1. `input_pdfs/`에 PDF 저장
2. `process-daily` 실행해 JSON 누적
3. 금요일 13시에 `send-weekly` 실행
4. 필요 시 `send_mode: draft`로 초안만 저장 후 검토

## 주의
- 원문 외 정보는 사용하지 않도록 프롬프트에 강하게 제한했습니다.
- PDF 추출 품질에 따라 원문 인용 줄바꿈이 다소 정리될 수 있습니다.
- 도표/이미지는 페이지 이미지와 함께 모델에 보내도록 구현했지만, 너무 큰 PDF는 비용/토큰이 증가할 수 있습니다.
