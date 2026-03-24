# add-design-system

**Name:** `add-design-system`
**Description:** 새 디자인 시스템의 크롤러 policy를 생성하는 스킬. DS 이름을 입력하면 policy JSON을 만들고, a11y 레포에서 이어받을 수 있는 DS 등록 정보를 출력.

---

## 실행 방법

### Step 1 — DS 정보 수집

사용자에게 확인한다:

1. **DS 이름** (표시명, 예: "Chakra UI")
2. **DS ID** (kebab-case 영문 소문자, 예: "chakra") — 제안 후 확인받기
3. **문서 도메인** (예: "chakra-ui.com")
4. **브랜드 색상** HEX — 모르면 WebFetch로 공식 사이트를 조회해 찾는다

### Step 2 — 컴포넌트 URL 조사

수집 대상 컴포넌트 패턴은 프로젝트 루트의 `components.json`에 정의되어 있다. 반드시 이 파일을 읽어 패턴 목록을 확인한 뒤 진행한다.

WebFetch로 문서 사이트 컴포넌트 목록 페이지를 조회해 `components.json`의 각 패턴 `keywords`에 해당하는 URL 경로를 찾는다.
찾은 URL을 사용자에게 보여주고 확인받는다.

해당 DS에 컴포넌트가 존재하지 않으면 `none`으로 기록한다.

### Step 3 — policy JSON 생성

`src/spec_harvester/infrastructure/config/policies/{ds-id}.json` 파일을 생성한다.

```json
{
  "domain": "{domain}",
  "seed_urls": ["https://{domain}/{component-path}/"],
  "allowed_paths_prefix": ["/{component-path}/"],
  "disallowed_paths_prefix": [],
  "max_depth": 1,
  "max_pages": 30,
  "rate_limit_ms": 1000,
  "user_agent": "SpecHarvesterCrawler/0.1",
  "respect_robots": true
}
```

규칙:

- `max_depth: 1` — seed URL 페이지만 수집
- `rate_limit_ms: 1000` — 민간 사이트는 1000ms 이상
- seed_urls와 allowed_paths_prefix를 컴포넌트별로 1:1 매칭
- `none`인 패턴은 seed_urls에 포함하지 않는다
- 모든 컴포넌트가 공통 prefix 하위에 있으면 `allowed_paths_prefix`를 단일 prefix로 지정 가능

### Step 4 — DS 등록 정보 출력

아래 형식으로 요약을 출력한다. 사용자가 a11y 레포에서 그대로 붙여넣을 수 있게 코드 블록으로 감싼다.

```
id:     {ds-id}
name:   {DS 표시명}
domain: {domain}
color:  {HEX}

pattern mappings:
  button           → {url-path-or-none}
  text-input       → {url-path-or-none}
  modal-dialog     → {url-path-or-none}
  toggle           → {url-path-or-none}
  tabs             → {url-path-or-none}
  tooltip          → {url-path-or-none}
  disclosure       → {url-path-or-none}
  accordion        → {url-path-or-none}
  select           → {url-path-or-none}
  alert-toast      → {url-path-or-none}
  form-validation  → {url-path-or-none}
  navigation-menu  → {url-path-or-none}
  pagination       → {url-path-or-none}
  date-picker      → {url-path-or-none}
  file-upload      → {url-path-or-none}
  carousel         → {url-path-or-none}
  tree             → {url-path-or-none}
```

없는 패턴은 `none`으로 표시한다.

### Step 5 — 완료 안내

다음 두 단계를 순서대로 안내한다:

**1. 크롤 실행:**

```bash
python -m spec_harvester crawl --policy {ds-id}
```

**2. a11y 레포에서 트랜스포머 등록:**

> a11y 레포 Claude Code 세션에서 `/register-design-system` 을 실행하고
> 위의 DS 등록 정보를 붙여넣으세요.
