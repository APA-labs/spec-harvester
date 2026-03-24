# manage-ds-crawl

**Name:** `manage-ds-crawl`
**Description:** 기존 디자인 시스템의 크롤 대상 컴포넌트를 수정하는 스킬. 컴포넌트 URL이 바뀌었거나 새 컴포넌트를 추가할 때 policy JSON 파일을 업데이트. 새 DS 추가는 `/add-design-system` 사용.

---

## 실행 방법

### Step 1 — 정보 수집

사용자에게 다음을 확인한다:

1. **대상 DS** — 현재 policy 파일 목록을 보여주고 선택받는다
   - `src/spec_harvester/infrastructure/config/policies/` 디렉토리의 JSON 파일 목록
2. **변경 내용** — 다음 중 하나:
   - 컴포넌트 URL 변경 (예: "Button이 /components/button-new/ 로 바뀜")
   - 컴포넌트 추가 (예: "Checkbox도 크롤하고 싶음")
   - 컴포넌트 제거

컴포넌트 URL이 불분명하면 WebFetch로 해당 DS 문서 사이트를 조회해 확인한다.
컴포넌트 추가 시 프로젝트 루트의 `components.json`에 정의된 패턴 목록을 기준으로 한다. 패턴에 없는 컴포넌트는 사용자에게 `components.json` 업데이트 여부를 먼저 확인한다.

### Step 2 — policy JSON 수정

`src/spec_harvester/infrastructure/config/policies/{ds-id}.json` 파일을 읽고 변경사항을 반영한다.

- URL 변경: `seed_urls`와 `allowed_paths_prefix` 동시 업데이트
- 컴포넌트 추가: 두 배열에 항목 추가, `max_pages` 필요 시 조정
- 컴포넌트 제거: 두 배열에서 항목 삭제

### Step 3 — 완료 안내

- 수정된 파일과 변경 내용 요약
- 크롤 재실행 명령어: `python -m spec_harvester crawl --policy {ds-id}`
- URL 변경이 있었다면 a11y 레포의 `SOURCE_URL_MAP`도 업데이트 필요함을 알린다
  > a11y 레포 Claude Code 세션에서 `/register-design-system` 을 실행하고
  > 변경된 URL 매핑을 알려주세요.
