# Image Poet 📸✨

이미지를 업로드하면 시를 생성해주는 AI 모바일 앱

## 🏗️ 프로젝트 구조

```
image-poet/
├── mobile/          # Flutter 모바일 앱
├── backend/         # Python FastAPI 백엔드
├── shared/          # 공통 자산 및 문서
├── scripts/         # 개발/배포 스크립트
└── .github/         # CI/CD 워크플로우
```

## 🚀 빠른 시작

### 전체 개발 환경 실행
```bash
./scripts/start-dev.sh
```

### 개별 실행
```bash
# 백엔드만
cd backend && uvicorn app.main:app --reload

# 모바일만
cd mobile && flutter run
```

## 🛠️ 기술 스택

- **Mobile**: Flutter (Dart)
- **Backend**: FastAPI (Python)
- **AI**: OpenAI GPT-4 Vision
- **Database**: PostgreSQL
- **Container**: Docker

## 📋 주요 기능

- [ ] 이미지 업로드/촬영
- [ ] AI 이미지 분석
- [ ] 시 자동 생성
- [ ] 시 저장 및 관리
- [ ] 공유 기능

## 🔧 개발 환경 설정

### 요구사항
- Flutter SDK 3.16+
- Python 3.11+
- Docker & Docker Compose

### 설치
```bash
git clone <repository>
cd image-poet
./scripts/setup.sh
```
