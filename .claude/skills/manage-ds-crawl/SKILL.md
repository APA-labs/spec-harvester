# manage-ds-crawl

**Name:** `manage-ds-crawl`
**Description:** 기존 디자인 시스템의 크롤 대상 컴포넌트를 수정하는 스킬. 컴포넌트 URL이 바뀌었거나 새 컴포넌트를 추가할 때 policy JSON 파일을 업데이트. 새 DS 추가는 `/add-design-system` 사용.

---

## 실행 방법

### Step 1 — 모드 선택

먼저 사용자에게 작업 유형을 확인한다:

**A. 특정 DS 수정** — 하나의 policy 파일을 직접 편집
**B. 전체 동기화** — `components.json`에 새 패턴이 추가됐을 때 모든 policy를 한 번에 업데이트

---

### 모드 A — 특정 DS 수정

#### A-1. 정보 수집

1. **대상 DS** — 현재 policy 파일 목록을 보여주고 선택받는다
   - `src/spec_harvester/infrastructure/config/policies/` 디렉토리의 JSON 파일 목록
2. **변경 내용** — 다음 중 하나:
   - 컴포넌트 URL 변경 (예: "Button이 /components/button-new/ 로 바뀜")
   - 컴포넌트 추가 (예: "Checkbox도 크롤하고 싶음")
   - 컴포넌트 제거

컴포넌트 URL이 불분명하면 WebFetch로 해당 DS 문서 사이트를 조회해 확인한다.
컴포넌트 추가 시 프로젝트 루트의 `components.json`에 정의된 패턴 목록을 기준으로 한다. 패턴에 없는 컴포넌트는 사용자에게 `components.json` 업데이트 여부를 먼저 확인한다.

#### A-2. policy JSON 수정

`src/spec_harvester/infrastructure/config/policies/{ds-id}.json` 파일을 읽고 변경사항을 반영한다.

- URL 변경: `seed_urls`와 `allowed_paths_prefix` 동시 업데이트
- 컴포넌트 추가: 두 배열에 항목 추가, `max_pages` 필요 시 조정
- 컴포넌트 제거: 두 배열에서 항목 삭제

#### A-3. 완료 안내

- 수정된 파일과 변경 내용 요약
- 크롤 재실행 명령어: `python -m spec_harvester crawl --policy {ds-id}`
- URL 변경이 있었다면 a11y 레포의 `SOURCE_URL_MAP`도 업데이트 필요함을 알린다
  > a11y 레포 Claude Code 세션에서 `/register-design-system` 을 실행하고
  > 변경된 URL 매핑을 알려주세요.

#### A-4. 마크다운 포맷팅 확인

크롤이 끝난 뒤, 저장된 `.md` 파일을 샘플로 하나 열어 다음을 확인한다:

1. **노이즈 라인 제거 여부** — 첫 줄에 CSS blob(`{...}`)이나 마지막에 `self.__next_f` 같은 JS 런타임 데이터가 없는지
2. **최대 줄 길이** — 500자를 넘는 줄이 없는지 (`max line length` 값 확인)
3. **빈 줄 밀도** — 연속 빈 줄이 2줄 이상 반복되지 않는지

문제가 발견되면 `src/spec_harvester/application/queue.py`의 `_clean_markdown` 함수를 수정한다:

- CSS/JS 노이즈: 줄 길이 임계값(`500`) 또는 공백 비율 임계값(`0.10`) 조정
- 연속 빈 줄: `re.sub(r"\n{3,}", ...)` 패턴 조정

---

### 모드 B — 전체 동기화 (components.json → 모든 policy)

`components.json`에 새 패턴이 추가됐을 때 모든 policy 파일에 해당 컴포넌트를 추가한다.

#### B-1. 현황 파악

1. `components.json`을 읽어 전체 패턴 목록을 확인한다
2. `src/spec_harvester/infrastructure/config/policies/` 의 모든 JSON 파일을 읽는다
3. 각 policy별로 **누락된 패턴**을 파악한다 (seed_urls에 없는 패턴 keywords 기준)

w3c.json / apg.json은 ARIA 스펙 문서이므로 동기화 대상에서 **제외**한다.

#### B-2. 누락 URL 조사

누락된 패턴이 있는 DS별로:

1. WebFetch로 해당 DS 문서 사이트의 컴포넌트 목록 페이지를 조회한다
2. 패턴 `keywords`에 해당하는 URL 경로를 찾는다
3. 해당 DS에 그 컴포넌트가 **존재하지 않으면** `none`으로 기록하고 넘어간다

#### B-3. policy 파일 일괄 업데이트

각 policy 파일에 대해:

- 찾은 URL을 `seed_urls`와 `allowed_paths_prefix`에 추가한다
- `allowed_paths_prefix`가 단일 공통 prefix 방식(예: `/primitives/docs/components/`)이면 추가 불필요
- seed URL 수가 늘어날 경우 `max_pages`를 적절히 조정한다 (seed 수 × 2 이상)
- `none`인 컴포넌트는 건너뛴다

#### B-4. 완료 보고

DS별로 추가된 컴포넌트 목록과 `none` 처리된 항목을 표 형태로 요약한다.

```
| DS      | 추가됨                        | 없음(skip)              |
|---------|-------------------------------|-------------------------|
| radix   | alert-dialog, toast, form     | pagination, date-picker |
| mui     | alert, snackbar, pagination   | -                       |
| ...     | ...                           | ...                     |
```

전체 재크롤이 필요하면:

```bash
for p in radix mui antd chakra react-aria; do
  python -m spec_harvester crawl --policy $p
done
```

#### B-5. 마크다운 포맷팅 확인

크롤이 끝난 뒤, DS별로 `.md` 파일을 샘플로 하나씩 열어 다음을 확인한다:

1. **노이즈 라인 제거 여부** — 첫 줄에 CSS blob(`{...}`)이나 마지막에 `self.__next_f` 같은 JS 런타임 데이터가 없는지
2. **최대 줄 길이** — 500자를 넘는 줄이 없는지 (`max line length` 값 확인)
3. **빈 줄 밀도** — 연속 빈 줄이 2줄 이상 반복되지 않는지

문제가 발견되면 `src/spec_harvester/application/queue.py`의 `_clean_markdown` 함수를 수정한다:

- CSS/JS 노이즈: 줄 길이 임계값(`500`) 또는 공백 비율 임계값(`0.10`) 조정
- 연속 빈 줄: `re.sub(r"\n{3,}", ...)` 패턴 조정
