# Spec Harvester Crawler

Crawler project scaffold with DDD-oriented package layout.

## Quick Start

```bash
python -m pip install -e .
python -m spec_crawler --help
python -m spec_crawler crawl --policy w3c --max-pages 10
```

## Project Layout

- `src/spec_crawler/domain`: domain models/rules
- `src/spec_crawler/application`: use-case orchestration
- `src/spec_crawler/infrastructure`: external adapters (http/storage/config/parsers)
- `src/spec_crawler/interfaces`: CLI and other interfaces

Detailed structure guide: `docs/DDD_ARCHITECTURE.md`
