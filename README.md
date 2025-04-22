# 일기 감정 분석 GitHub 상태 업데이트

Notion 일기의 감정을 분석하여 GitHub 프로필 상태를 자동으로 업데이트합니다.

## 주요 기능

- Notion 일기 최근 10개 항목 조회
- KoELECTRA 감정 분석 모델을 사용한 텍스트 감정 분석
  - 7가지 감정 분류: 기쁨, 슬픔, 분노, 두려움, 놀람, 혐오, 중립
  - 최근 일기에 더 높은 가중치 부여 (시간 기반 가중치 시스템)
- 분석된 감정에 따른 GitHub 프로필 상태 자동 업데이트
  - 이모지와 상태 메시지 설정
  - 전반적인 감정 상태 반영
- GitHub Actions를 통한 자동 실행

## 설치 방법

1. Poetry 설치 (파이썬 패키지 관리자)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. 저장소 복제
   ```bash
   git clone https://github.com/your-username/diary-emotion-action.git
   cd diary-emotion-action
   ```

3. 의존성 설치
   ```bash
   poetry install
   ```

## 환경 설정

1. GitHub 저장소에 필요한 시크릿 설정:
   - `NOTION_TOKEN`: Notion API 통합 토큰
     - [Notion API 설정 페이지](https://www.notion.so/my-integrations)에서 생성
   - `NOTION_DATABASE_ID`: Notion 일기 데이터베이스 ID
     - 데이터베이스 URL에서 추출 가능
     - 예: `https://notion.so/workspace/{DATABASE_ID}?v=...`
   - `GITHUB_TOKEN`: GitHub 개인 접근 토큰
     - [GitHub 토큰 설정](https://github.com/settings/tokens)에서 생성
     - 필요한 권한: `user` 스코프 (프로필 상태 업데이트용)

2. Notion 데이터베이스 요구사항:
   - 필수 속성:
     - `Content`: 일기 내용 (텍스트)
     - `Date`: 작성일 (날짜)

3. GitHub Actions 워크플로우 설정:
   - `.github/workflows/sentiment-status.yml` 파일에서 실행 주기 설정
   - 기본값: 00시 실행

## 개발 환경 설정

```bash
# 가상 환경 활성화
poetry env activate

# 테스트 실행
poetry run pytest

# 코드 포맷팅
poetry run black .
poetry run isort .
```

## 감정 분석 시스템

- 최근 10개 일기 항목 분석
- 시간 기반 가중치 적용:
  - 오늘 작성: 1.0
  - 하루 지날 때마다 0.15씩 감소
  - 최소 가중치: 0.1
- 각 일기의 감정 분석 결과와 가중치를 종합하여 최종 감정 상태 결정

## 상태 메시지 예시

- 😄 "Been feeling pretty good lately!"
- 😢 "Going through some emotions..."
- 😠 "Taking deep breaths"
- 😨 "Dealing with some uncertainty"
- 😲 "Life's been full of surprises!"
- 🤢 "Need a change of pace"
- 😐 "Keeping it steady"

## 라이선스

MIT

## 기여하기

버그 리포트, 기능 제안, 풀 리퀘스트 모두 환영합니다!

1. 이슈 생성
2. 브랜치 생성
3. 변경사항 커밋
4. 풀 리퀘스트 생성 