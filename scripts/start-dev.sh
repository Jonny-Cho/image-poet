#!/bin/bash

echo "🚀 Starting Image Poet Development Environment"

# 환경 변수 체크
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요."
fi

# Docker Compose로 백엔드 시작
echo "🐍 Starting Backend with Docker..."
docker-compose up -d

echo "✅ Backend: http://localhost:8000"
echo "✅ Database: localhost:5432"
echo ""
echo "📱 Flutter 앱을 실행하려면:"
echo "   cd mobile && flutter run"