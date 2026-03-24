# Spec Harvester

W3C 사양 문서 등 기술 명세를 수집하는 DDD 기반 웹 크롤러입니다.
robots.txt 준수, 요청 속도 제한, SHA256 기반 콘텐츠 중복 제거를 지원합니다.

## 설치

Python 3.11 이상 필요.

```bash
python -m pip install -e .
python -m spec_harvester --help  # 설치 확인
```

## 사용법

### crawl — 문서 수집

```bash
# w3c 정책으로 최대 10페이지 수집
python -m spec_harvester crawl --policy w3c --max-pages 10
```

| 옵션 | 설명 |
|------|------|
| `--policy` | 사용할 정책 이름 (정책 파일명과 일치해야 함) |
| `--max-pages` | 최대 수집 페이지 수 (정책 파일의 `max_pages`를 덮어씀) |

수집 결과:

```
storage/raw/YYYY-MM-DD/<sha256>.html|pdf|bin
storage/raw/YYYY-MM-DD/<sha256>.meta.json
storage/manifests/run-<id>.json
storage/manifests/url_index.json
logs/run-<id>.jsonl
```

### reset — 재크롤링을 위한 초기화

```bash
# url_index만 초기화 (파일은 유지, 다음 crawl 시 전체 재수집)
python -m spec_harvester reset

# url_index + raw 파일 모두 삭제
python -m spec_harvester reset --storage
```

url_index.json은 ETag/SHA256 기반 중복 체크에 사용됩니다. 파일이 삭제됐는데 crawl이 `no_change`만 반환할 때 실행하세요.

### audit — 수집 결과 검증

```bash
python -m spec_harvester audit
python -m spec_harvester audit --manifest-root storage/manifests
```

manifest에 기록된 파일의 존재 여부와 SHA256 무결성을 검사하고 보고서를 출력합니다.

### publish — 공유용 번들 생성

```bash
# 가장 최근 run 기준으로 번들 생성
python -m spec_harvester publish

# 특정 run-id 기준
python -m spec_harvester publish --run-id 20260228T014916794323Z

# 출력 디렉터리 지정
python -m spec_harvester publish --output-dir exports
```

`exports/spec-harvester-run-<run_id>.tar.gz` 파일이 생성됩니다.
번들에는 manifest 파일과 JSONL 로그가 포함됩니다.

## Policy 파일

경로: `src/spec_harvester/infrastructure/config/policies/<name>.json`

### 기본 제공 Policy

| 정책 파일 | 대상 사이트 | 수집 범위 |
|-----------|-------------|-----------|
| `w3c` | www.w3.org | WAI-ARIA 1.2, HTML-ARIA, AccName 1.2 스펙 |
| `apg` | www.w3.org | ARIA Authoring Practices Guide 패턴 |
| `mui` | mui.com | Material UI 컴포넌트 문서 |
| `radix` | www.radix-ui.com | Radix UI Primitives 컴포넌트 문서 |
| `antd` | ant.design | Ant Design 컴포넌트 문서 |

각 정책으로 크롤링:

```bash
python -m spec_harvester crawl --policy w3c
python -m spec_harvester crawl --policy mui
python -m spec_harvester crawl --policy radix
python -m spec_harvester crawl --policy antd

# 전체 정책 순서대로 실행
python -m spec_harvester crawl --policy all
```

### 새 디자인시스템 추가하기

수집 대상 컴포넌트 패턴은 프로젝트 루트의 **`components.json`** 에 정의되어 있습니다.
새 policy의 `seed_urls`와 `allowed_paths_prefix`는 이 파일의 패턴 키워드에 해당하는 URL만 포함합니다.

1. `components.json`을 열어 수집할 패턴 확인

2. `src/spec_harvester/infrastructure/config/policies/<이름>.json` 파일 생성:

```json
{
  "domain": "example.com",
  "seed_urls": [
    "https://example.com/docs/components/button",
    "https://example.com/docs/components/dialog"
  ],
  "allowed_paths_prefix": [
    "/docs/components/button",
    "/docs/components/dialog"
  ],
  "disallowed_paths_prefix": [],
  "max_depth": 1,
  "max_pages": 30,
  "rate_limit_ms": 1000,
  "user_agent": "SpecHarvesterCrawler/0.1",
  "respect_robots": true
}
```

3. 실행:

```bash
python -m spec_harvester crawl --policy <이름>
```

> **컴포넌트 패턴 추가/변경** 시에는 `components.json`을 먼저 수정하고, 관련 policy 파일과 이 README를 함께 업데이트합니다.

**필드 설명:**

| 필드 | 필수 | 설명 |
|------|------|------|
| `domain` | ✅ | 크롤링 대상 도메인 (이 도메인 외 링크는 무시) |
| `seed_urls` | ✅ | 크롤링 시작 URL 목록 |
| `allowed_paths_prefix` | — | 허용할 경로 prefix 목록 (빈 배열이면 전체 허용) |
| `disallowed_paths_prefix` | — | 제외할 경로 prefix 목록 |
| `max_depth` | — | seed URL 기준 최대 링크 탐색 깊이 |
| `max_pages` | — | 최대 수집 페이지 수 |
| `rate_limit_ms` | — | 요청 간격 (밀리초) |
| `respect_robots` | — | robots.txt 준수 여부 |

## 저장 구조

```
storage/
  raw/
    YYYY-MM-DD/
      <domain>/
        <sha256>.html | <sha256>.pdf | <sha256>.bin   # 수집된 원본 파일
        <sha256>.meta.json                             # URL, 상태코드, 헤더 등 메타데이터
  manifests/
    run-<id>.json       # 해당 run에서 수집된 URL 목록
    url_index.json      # 전체 URL → 파일 매핑 인덱스

logs/
  run-<id>.jsonl        # run_started / fetch_success / fetch_error / saved / dedup_hit / run_finished
```

`meta.json` 주요 필드: `url`, `fetched_at`, `status`, `content_type`, `sha256`, `bytes`, `final_url`, `headers.etag`, `headers.last-modified`

## 트러블슈팅

**`No module named spec_harvester`**
→ `python -m pip install -e .` 실행

**`policy file not found`**
→ `--policy w3c` 지정 시 `w3c.json`이 policies 폴더에 있어야 함

**`domain must be a non-empty string` / `seed_urls must not be empty`**
→ policy 파일에서 필수 필드 확인

**두 번째 실행에서 파일이 저장되지 않음**
→ 정상 동작. ETag / Last-Modified / SHA256이 동일하면 `no_change`로 처리됨
→ `audit` 명령으로 현황 확인

**`fetch_error`가 반복됨**
→ `logs/run-*.jsonl`에서 이벤트 타입이 `fetch_error`인 항목의 `reason` 필드 확인

## 아키텍처

DDD 레이어 구조 (`interfaces → application → domain`, infrastructure는 주입):

- `domain/` — URL 정규화, 해싱, 메타데이터 모델 (외부 의존성 없음)
- `application/` — BFS 크롤 오케스트레이터, audit, publish 유스케이스
- `infrastructure/` — HTTP 클라이언트, robots.txt, 속도 제한, 파일 저장, JSONL 로깅
- `interfaces/` — CLI 진입점

상세 문서: [`docs/DDD_ARCHITECTURE.md`](docs/DDD_ARCHITECTURE.md)
