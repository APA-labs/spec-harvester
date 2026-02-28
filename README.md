# Spec Harvester

W3C 문서 수집을 위한 DDD 기반 크롤러입니다.

## 1) 설치

요구사항:
- Python 3.11+

설치:

```bash
python -m pip install -e .
```

CLI 확인:

```bash
python -m spec_harvester --help
```

## 2) Crawl 실행 예시

기본 실행:

```bash
python -m spec_harvester crawl --policy w3c --max-pages 10
```

실행 결과 예:
- `storage/raw/YYYY-MM-DD/*.html|*.pdf`
- `storage/raw/YYYY-MM-DD/*.meta.json`
- `storage/manifests/run-<id>.json`
- `storage/manifests/url_index.json`
- `logs/run-<id>.jsonl`

Audit 실행:

```bash
python -m spec_harvester audit
```

특정 manifest 경로로 감사:

```bash
python -m spec_harvester audit --manifest-root storage/manifests
```

Publish 실행(공유용 번들 생성):

```bash
# 최신 run 기준
python -m spec_harvester publish

# 특정 run-id 기준
python -m spec_harvester publish --run-id 20260228T014916794323Z
```

생성 결과:
- `exports/spec-harvester-run-<run_id>.tar.gz`

## 3) Policy 파일 수정 방법

정책 파일 경로:
- `src/spec_harvester/infrastructure/config/policies/w3c.json`

예시 필드:

```json
{
  "domain": "www.w3.org",
  "seed_urls": ["https://www.w3.org/TR/"],
  "allowed_paths_prefix": ["/TR/"],
  "disallowed_paths_prefix": ["/blog/"],
  "max_depth": 3,
  "max_pages": 200,
  "rate_limit_ms": 700,
  "user_agent": "SpecHarvesterCrawler/0.1",
  "respect_robots": true
}
```

주의:
- `domain`은 필수이며 빈 값이면 로드 실패
- `seed_urls`는 필수이며 비어 있으면 로드 실패

## 4) 저장 구조 설명

```text
storage/
  raw/
    YYYY-MM-DD/
      <sha256>.html | <sha256>.pdf | <sha256>.bin
      <sha256>.meta.json
  manifests/
    run-<command_id>.json
    url_index.json

logs/
  run-<command_id>.jsonl
```

`meta.json` 주요 필드:
- `url`, `fetched_at`, `status`, `content_type`
- `sha256`, `bytes`
- `headers.etag`, `headers.last-modified`
- `final_url`

## 5) 흔한 에러와 해결

1. `No module named spec_harvester`
- 원인: 패키지 설치 전 실행
- 해결: `python -m pip install -e .`

2. `policy file not found`
- 원인: `--policy` 이름과 JSON 파일명 불일치
- 해결: 예) `--policy w3c`면 `w3c.json`이 존재해야 함

3. `domain must be a non-empty string` / `seed_urls must not be empty`
- 원인: policy 필수 필드 누락/오입력
- 해결: 정책 파일 값 보완

4. 수집 실패(`fetch_error`)가 반복됨
- 원인: 네트워크/DNS/대상 서버 문제
- 해결: `logs/run-*.jsonl`에서 `fetch_error` 원인 확인 후 재시도

5. 두 번째 실행에서 저장이 안 됨
- 정상 동작일 수 있음: ETag/Last-Modified/sha256 기반 `no_change` 감지
- 확인: `storage/manifests/url_index.json`, `audit` 결과

## 6) 아키텍처

DDD 레이어 구조:
- `src/spec_harvester/domain`
- `src/spec_harvester/application`
- `src/spec_harvester/infrastructure`
- `src/spec_harvester/interfaces`

상세 문서:
- `docs/DDD_ARCHITECTURE.md`
