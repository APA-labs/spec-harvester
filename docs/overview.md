# spec-harvester 개요

## 무엇을 하는 도구인가

spec-harvester는 **접근성 관련 기술 문서를 크롤링해 로컬에 저장하는 Python 도구**다.

수집 대상:

- **W3C ARIA APG** (`www.w3.org`) — ARIA 패턴 스펙, 체크리스트의 원본
- **MUI** (`mui.com`) — Material UI 컴포넌트 접근성 가이드
- **Radix UI** (`www.radix-ui.com`) — Radix 프리미티브 접근성 문서
- **Ant Design** (`ant.design`) — Ant Design 컴포넌트 문서

크롤 결과는 원본 HTML 파일로 저장된다. 이 결과를 **a11y 모노레포의 `spec-transformer`** 가 Claude API를 통해 구조화된 rule JSON으로 변환한다.

## 전체 파이프라인에서의 위치

```
spec-harvester           spec-transformer (a11y 레포)      backend
(이 레포)             →   tools/spec-transformer/       →   packages/backend/src/rules/
 W3C + DS 문서 크롤        Claude API로 rule 추출             런타임에 Claude 컨텍스트로 사용
 → storage/raw/            → *.json, patterns.ts
```

## 실행 주기

분기 1회 수동 실행. W3C 스펙이나 DS 문서가 크게 바뀌었을 때 재실행.

```bash
python -m spec_harvester crawl --policy apg
python -m spec_harvester crawl --policy mui
python -m spec_harvester crawl --policy radix
python -m spec_harvester crawl --policy antd
```

## 관련 문서

- [도메인 개념](domain-concepts.md) — Policy, FetchMeta, 해싱, BFS 큐
- [출력 형식](output-format.md) — storage/ 구조, meta.json 스키마
- [Policy 관리](policies.md) — 현재 policy 목록, 추가 방법
- [아키텍처](architecture.md) — 레이어 구조
