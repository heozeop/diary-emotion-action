# Diary Emotion GitHub Status Action

Notion 일기의 감정을 분석하여 GitHub 프로필 상태를 자동으로 업데이트하는 GitHub Action입니다.

## 주요 기능

- Notion 일기 최근 10개 항목의 감정 분석
- 시간 기반 가중치가 적용된 감정 분석
- GitHub 프로필 상태 자동 업데이트

## 사용 방법

1. GitHub 저장소에 시크릿 설정:
   - `NOTION_TOKEN`
   - `NOTION_DATABASE_ID`
   - `GITHUB_TOKEN`

2. 워크플로우 파일 생성 (`.github/workflows/update-status.yml`):

```yaml
name: Update GitHub Status

on:
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다 실행
  workflow_dispatch:        # 수동 실행 가능

jobs:
  update-status:
    runs-on: ubuntu-latest
    steps:
      - name: Update Status
        uses: your-username/diary-emotion-action@v1
        with:
          notion_token: ${{ secrets.NOTION_TOKEN }}
          notion_database_id: ${{ secrets.NOTION_DATABASE_ID }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## 입력 파라미터

| 파라미터 | 필수 | 기본값 | 설명 |
|----------|------|--------|------|
| `notion_token` | ✅ | - | Notion API 통합 토큰 |
| `notion_database_id` | ✅ | - | Notion 일기 데이터베이스 ID |
| `github_token` | ✅ | - | GitHub 토큰 (user 스코프 필요) |
| `entries_limit` | ❌ | 10 | 분석할 최근 일기 수 |
| `model_name` | ❌ | circulus/koelectra-emotion-v1 | 감정 분석 모델 이름 |

## Notion 데이터베이스 요구사항

필수 속성:
- `Content`: 일기 내용 (텍스트)
- `Date`: 작성일 (날짜)

## 감정 분석 시스템

- 시간 기반 가중치:
  - 오늘 작성: 1.0
  - 하루 지날 때마다 0.15씩 감소
  - 최소 가중치: 0.1

## 상태 메시지 예시

- 😄 "Been feeling pretty good lately!"
- 😢 "Going through some emotions..."
- 😠 "Taking deep breaths"
- 😨 "Dealing with some uncertainty"
- 😲 "Life's been full of surprises!"
- 🤢 "Need a change of pace"
- 😐 "Keeping it steady"

## 개발하기

1. 저장소 복제
```bash
git clone https://github.com/your-username/diary-emotion-action.git
```

2. 의존성 설치
```bash
poetry install
```

3. 테스트 실행
```bash
poetry run pytest
```

## 라이선스

MIT

## 기여하기

버그 리포트, 기능 제안, 풀 리퀘스트 모두 환영합니다!

1. 이슈 생성
2. 브랜치 생성
3. 변경사항 커밋
4. 풀 리퀘스트 생성 