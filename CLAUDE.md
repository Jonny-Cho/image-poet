# Claude 개발 가이드 📖

Image Poet 프로젝트에서 Claude Code를 사용한 개발 가이드입니다.

## 🚨 중요 규칙

### Commit & PR 작성 규칙
**❌ 절대 금지**: 모든 commit 메시지와 PR에서 Claude 관련 언급 완전 금지

```bash
# ❌ 금지 사항
🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>

# ✅ 올바른 예시
feat: Add user authentication system

- Implement JWT-based authentication
- Add login/logout functionality
- Create user registration flow
```

### 이유
- 프로페셔널한 코드베이스 유지
- AI 도구 사용 흔적 제거
- 순수한 개발 히스토리 보존

## 🛠️ 개발 워크플로우

### 1. 기능 개발
```bash
# 새 브랜치 생성
git checkout -b feature/new-feature

# Claude와 함께 개발
# ... 개발 작업 ...

# 커밋 (Claude 언급 없이)
git commit -m "feat: Add new feature

- Implement core functionality
- Add comprehensive tests
- Update documentation"
```

### 2. PR 생성
```bash
# PR 생성 (Claude 언급 없이)
gh pr create --title "feat: Add new feature" --body "
## Summary
• Core functionality implementation
• Test coverage added
• Documentation updated

## Test Plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
"
```

## 📝 개발 패턴

### Flutter 앱 구조
```
mobile/
├── lib/
│   ├── screens/          # 화면 위젯
│   ├── widgets/          # 재사용 컴포넌트
│   ├── services/         # API 통신
│   ├── models/           # 데이터 모델
│   └── utils/            # 유틸리티
```

### Python API 구조
```
backend/
├── app/
│   ├── api/              # API 라우터
│   ├── models/           # DB 모델
│   ├── services/         # 비즈니스 로직
│   ├── core/             # 설정, 인증
│   └── tests/            # 테스트
```

## 🔧 도구 사용법

### 개발 환경 실행
```bash
# 전체 환경 시작
./scripts/start-dev.sh

# 개별 실행
cd mobile && flutter run        # Flutter 앱
cd backend && uvicorn app.main:app --reload  # Python API
```

### 테스트 실행
```bash
# 백엔드 테스트
cd backend && pytest

# 모바일 테스트
cd mobile && flutter test
```

## 📋 코드 품질

### Commit 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 코드
chore: 빌드, 설정 변경
```

### 코드 리뷰 체크리스트
- [ ] 테스트 커버리지 충분한가?
- [ ] 에러 핸들링이 적절한가?
- [ ] 성능 이슈는 없는가?
- [ ] 보안 취약점은 없는가?
- [ ] 문서가 업데이트되었는가?

## 🚀 배포 프로세스

### 1. 개발 완료
- 모든 테스트 통과
- 코드 리뷰 완료
- 문서 업데이트

### 2. PR 머지
- main 브랜치로 머지
- CI/CD 파이프라인 실행
- 자동 배포 (설정된 경우)

### 3. 릴리즈
```bash
# 태그 생성
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## 💡 개발 팁

### AI 도구 활용
- 코드 생성 시 Claude 활용
- 디버깅 도움 요청
- 코드 리뷰 및 개선 제안
- 문서 작성 지원

### 주의사항
- **절대 Claude 언급을 commit/PR에 포함하지 말 것**
- 생성된 코드는 반드시 검토 후 사용
- 보안에 민감한 정보는 Claude와 공유 금지
- 테스트 코드 작성 필수

## 📞 문제 해결

### 자주 발생하는 이슈
1. **테스트 실패**: `pytest` 또는 `flutter test` 실행
2. **빌드 오류**: 의존성 확인 및 재설치
3. **Docker 문제**: `docker-compose down && docker-compose up`

### 도움 요청
- 이슈는 GitHub Issues에 등록
- 복잡한 문제는 팀 회의에서 논의
- Claude 도움이 필요한 경우 가이드 준수