# 도메인 개념

## Policy

크롤 대상을 정의하는 설정 단위. `src/spec_harvester/infrastructure/config/policies/*.json` 에 저장.

```json
{
  "domain": "www.w3.org",
  "seed_urls": ["https://www.w3.org/WAI/ARIA/apg/patterns/"],
  "allowed_paths_prefix": ["/WAI/ARIA/apg/patterns/"],
  "disallowed_paths_prefix": ["/WAI/ARIA/apg/patterns/landmarks/"],
  "max_depth": 2,
  "max_pages": 60,
  "rate_limit_ms": 700,
  "user_agent": "SpecHarvesterCrawler/0.1",
  "respect_robots": true
}
```

| 필드                      | 역할                                           |
| ------------------------- | ---------------------------------------------- |
| `seed_urls`               | BFS 시작점. 여기서부터 링크를 따라간다.        |
| `allowed_paths_prefix`    | 이 경로로 시작하는 URL만 수집                  |
| `disallowed_paths_prefix` | 이 경로는 무조건 제외                          |
| `max_depth`               | seed에서 몇 단계 깊이까지 따라갈지             |
| `max_pages`               | 수집할 최대 페이지 수                          |
| `rate_limit_ms`           | 요청 간격 (ms). 민간 사이트는 1000ms 이상 권장 |

## URL 정규화

크롤러는 수집 전 URL을 정규화한다:

- 트레일링 슬래시 통일
- fragment(#) 제거
- 쿼리스트링 제거

정규화된 URL이 `allowed_paths_prefix`에 매칭되는지 검사한다.

## FetchMeta

페이지 하나를 수집한 결과를 나타내는 도메인 객체 (`domain/meta.py`).

```python
@dataclass
class FetchMeta:
    url: str          # 정규화된 최종 URL
    fetched_at: str   # ISO 8601 타임스탬프
    status: int       # HTTP 상태 코드
    content_type: str
    sha256: str       # 본문 SHA-256 해시 (파일명으로 사용)
    bytes: int        # 본문 크기
    headers: dict     # etag, last-modified
    final_url: str    # 리다이렉트 후 최종 URL
```

## SHA-256 해싱과 중복 제거

수집한 HTML 본문을 SHA-256으로 해시하여 파일명으로 사용한다:

- `{sha256}.html` — 본문
- `{sha256}.meta.json` — 메타데이터

같은 내용의 페이지가 여러 URL에서 크롤되면 해시가 같으므로 자동으로 중복 제거된다.

ETag/Last-Modified 헤더가 있으면 재크롤 시 304 응답으로 변경 여부를 감지한다.

## BFS 크롤 큐

`application/queue.py`가 BFS 방식으로 URL을 처리한다:

1. seed_urls를 큐에 추가
2. 큐에서 URL을 꺼내 fetch
3. HTML 파싱해 링크 추출
4. `allowed_paths_prefix` 조건을 충족하고 아직 방문하지 않은 URL을 큐에 추가
5. `max_depth`와 `max_pages` 초과 시 중단

방문한 URL 집합을 메모리에 유지해 재방문을 방지한다.
