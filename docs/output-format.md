# 출력 형식

## 디렉토리 구조

```
storage/
└── raw/
    └── YYYY-MM-DD/           # 크롤 실행 날짜
        ├── www.w3.org/       # 도메인별 분리
        │   ├── {sha256}.html
        │   ├── {sha256}.meta.json
        │   └── ...
        ├── mui.com/
        ├── www.radix-ui.com/
        └── ant.design/
```

날짜 디렉토리는 크롤 시작 시점의 UTC 날짜 기준으로 생성된다.

## meta.json 스키마

각 HTML 파일에 대응하는 메타데이터 파일. `spec-transformer`가 이 파일로 URL을 확인한다.

```json
{
  "url": "https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/examples/checkbox-mixed",
  "fetched_at": "2026-03-24T04:44:41.863756Z",
  "status": 200,
  "content_type": "text/html; charset=utf-8",
  "sha256": "033d949749abea53d25f4b69ceac5ca17f0e25bf6dd111357e5bd190c68abc61",
  "bytes": 46798,
  "headers": {
    "etag": null,
    "last-modified": "Wed, 18 Mar 2026 23:07:28 GMT"
  },
  "final_url": "https://www.w3.org/WAI/ARIA/apg/patterns/checkbox/examples/checkbox-mixed/"
}
```

| 필드           | 설명                          |
| -------------- | ----------------------------- |
| `url`          | 요청한 URL (정규화 전)        |
| `final_url`    | 리다이렉트 후 최종 URL        |
| `sha256`       | HTML 본문 해시. 파일명과 동일 |
| `headers.etag` | 재크롤 시 변경 감지용         |

## spec-transformer가 meta.json을 사용하는 방식

`tools/spec-transformer/src/reader.ts`는 `*.meta.json` 파일을 먼저 읽어 URL을 확인하고, URL이 원하는 패턴과 매칭되면 동일 해시의 `.html` 파일을 읽는다.

```
reader.ts 동작:
1. storage/raw/YYYY-MM-DD/**/*.meta.json 전체 탐색
2. meta.json의 url 필드로 패턴 매칭 (예: /WAI/ARIA/apg/patterns/button/)
3. 매칭되면 {sha256}.html 읽기
4. extractor.ts에 HTML 전달
```

## 크롤 결과 검증

```bash
python scripts/verify_crawl.py --input storage/raw/2026-03-24
```

policy의 `allowed_paths_prefix`와 `components.json`의 패턴 키워드를 기준으로 예상 URL이 수집됐는지 확인한다.
