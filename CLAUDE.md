# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install
python -m pip install -e .

# Run CLI
python -m spec_harvester --help

# Tests
pytest
pytest tests/test_crawl_orchestrator.py                                          # single file
pytest tests/test_crawl_orchestrator.py::test_run_crawl_creates_raw_manifest_and_logs  # single test
```

## CLI Commands

```bash
python -m spec_harvester crawl --policy w3c --max-pages 10
python -m spec_harvester audit --manifest-root storage/manifests
python -m spec_harvester publish --run-id <run_id> --output-dir exports
```

## Architecture

The project follows DDD layered architecture. Dependency rule: `interfaces → application → domain`; infrastructure is injected in, never imported by domain.

### Layers

- **`domain/`** — Pure domain models: `policy.py` (crawl rules), `url.py` (normalization/dedup), `hashing.py` (SHA256), `meta.py` (document metadata). No external dependencies.
- **`application/`** — Use cases: `queue.py` (BFS crawl orchestrator with depth/page limits), `audit.py` (manifest validation), `publish.py` (artifact bundling to tar.gz).
- **`infrastructure/`** — Adapters: HTTP client with retry/timeout, robots.txt parser, rate limiter, HTML link extractor, file writer (HTML/PDF/binary by content-type), manifest store (ETag/Last-Modified/SHA256 change detection), JSONL event logger.
- **`interfaces/`** — CLI entry point (`cli.py`), argument parsing for all three commands.

### Storage Layout

```
storage/raw/YYYY-MM-DD/<domain>/<sha256>.{html,pdf,bin}   # crawled content
storage/raw/YYYY-MM-DD/<domain>/<sha256>.meta.json         # per-file metadata
storage/manifests/run-<id>.json                   # per-run manifest
storage/manifests/url_index.json                  # global URL index
logs/run-<id>.jsonl                               # JSONL event log
exports/spec-harvester-run-<id>.tar.gz            # published bundles
```

### JSONL Log Events

Events: `run_started`, `fetch_success`, `fetch_error`, `saved`, `dedup_hit`, `run_finished`

## Component Patterns

수집 대상 컴포넌트 패턴은 `components.json`(프로젝트 루트)에 정의되어 있다.
새 디자인시스템 policy를 만들거나 수집 범위를 판단할 때 이 목록을 기준으로 한다.

| id | 해당하는 컴포넌트 키워드 |
|----|--------------------------|
| `button` | Button, IconButton |
| `text-input` | Input, TextField, TextInput |
| `modal-dialog` | Modal, Dialog, Drawer |
| `toggle` | Switch, Toggle, ToggleButton |
| `tabs` | Tabs, TabList |
| `tooltip` | Tooltip, Popover |
| `disclosure` | Accordion, Collapse, Disclosure |
| `accordion` | Accordion, Collapse |
| `select` | Select, Combobox, Dropdown |

- 새 디자인시스템 policy의 `seed_urls`와 `allowed_paths_prefix`는 이 9개 패턴에 해당하는 URL만 포함한다.
- W3C(`w3c.json`)와 APG(`apg.json`)도 이 패턴들의 ARIA 스펙 범위로 제한되어 있다.

## Git Workflow

- Branch naming: `codex/` prefix
- Flow: main → new branch → implement → commit → PR → merge → main
- Destructive git commands require explicit user approval
