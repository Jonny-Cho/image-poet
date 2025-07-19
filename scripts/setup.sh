#!/bin/bash

echo "🛠️ Setting up Image Poet Development Environment"

# 권한 설정
chmod +x scripts/*.sh

# Flutter 의존성 설치
echo "📱 Installing Flutter dependencies..."
cd mobile && flutter pub get && cd ..

# Python 가상환경 생성 및 의존성 설치 (선택사항)
echo "🐍 Setting up Python environment..."
cd backend
if command -v python3 &> /dev/null; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi
cd ..

# 환경 변수 템플릿 생성
if [ ! -f .env ]; then
    echo "📄 Creating .env template..."
    cat > .env << EOF
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=postgresql://imagepoet:password@localhost:5432/imagepoet

# JWT Secret
JWT_SECRET=your_jwt_secret_here
EOF
fi

echo "✅ Setup complete!"
echo ""
echo "다음 단계:"
echo "1. .env 파일에 OpenAI API 키를 설정하세요"
echo "2. ./scripts/start-dev.sh 로 개발 환경을 시작하세요"