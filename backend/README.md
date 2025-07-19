# Image Poet Backend API 🐍

Python FastAPI로 개발된 이미지 시 생성 백엔드

## 🚀 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 API 엔드포인트

- `GET /`: 서버 상태 확인
- `GET /health`: 헬스 체크
- `POST /poems/generate`: 이미지에서 시 생성 (예정)

## 🛠️ 주요 모듈

- `app/main.py`: FastAPI 앱 설정
- `app/models/`: 데이터베이스 모델
- `app/services/`: 비즈니스 로직 (AI, 이미지 처리)
- `app/api/`: API 라우터
- `app/core/`: 설정, 인증, 유틸리티