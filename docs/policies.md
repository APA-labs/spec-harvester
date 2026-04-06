# Policy 관리

## 현재 지원 Policy

| Policy ID | 도메인           | 수집 대상                | max_pages |
| --------- | ---------------- | ------------------------ | --------- |
| `apg`     | www.w3.org       | W3C ARIA APG 패턴 스펙   | 60        |
| `mui`     | mui.com          | MUI 컴포넌트 접근성 문서 | 30        |
| `radix`   | www.radix-ui.com | Radix UI 프리미티브 문서 | 30        |
| `antd`    | ant.design       | Ant Design 컴포넌트 문서 | 30        |
| `w3c`     | www.w3.org       | W3C 기술 명세 (레거시)   | —         |

> `apg`가 W3C ARIA 스펙의 주 소스다. `w3c`는 CSS 등 다른 스펙도 포함하므로 접근성 규칙 추출에는 `apg`를 사용한다.

## 크롤 실행

```bash
python -m spec_harvester crawl --policy apg    # W3C ARIA APG
python -m spec_harvester crawl --policy mui
python -m spec_harvester crawl --policy radix
python -m spec_harvester crawl --policy antd
python -m spec_harvester crawl --policy all    # 전체
```

## 수집 대상 컴포넌트 패턴

`components.json`에 정의된 패턴이 크롤 범위의 기준이다. Policy의 `allowed_paths_prefix`는 이 패턴들에 해당하는 URL만 포함해야 한다.

현재 패턴: `button`, `text-input`, `modal-dialog`, `toggle`, `tabs`, `tooltip`, `disclosure`, `accordion`, `select`

## Policy 수정 (기존 DS)

Cursor 세션에서 `/manage-ds-crawl` 스킬 실행.

URL이 바뀌었거나 새 컴포넌트를 추가할 때 `seed_urls`와 `allowed_paths_prefix`를 동시에 업데이트한다.

## 새 DS Policy 추가

Cursor 세션에서 `/add-design-system` 스킬 실행.

실행 결과로 출력되는 DS 등록 정보를 **a11y 레포의 `/register-design-system`** 에 붙여넣어야 트랜스포머에도 반영된다.

## Policy 파일 직접 수정 시 주의사항

- `seed_urls`와 `allowed_paths_prefix`는 항상 1:1 매칭이어야 한다
- `allowed_paths_prefix`에 없는 URL은 크롤러가 따라가지 않는다
- `max_depth: 1`은 seed URL 페이지만, `max_depth: 2`는 seed에서 링크된 페이지까지 수집
