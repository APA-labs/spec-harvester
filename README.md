# Spec Harvester Crawler

Crawler project scaffold with DDD-oriented package layout.

## Quick Start

```bash
python -m pip install -e .
python -m spec_harvester --help
python -m spec_harvester crawl --policy w3c --max-pages 10
```

## Project Layout

- `src/spec_harvester/domain`: domain models/rules
- `src/spec_harvester/application`: use-case orchestration
- `src/spec_harvester/infrastructure`: external adapters (http/storage/config/parsers)
- `src/spec_harvester/interfaces`: CLI and other interfaces

Detailed structure guide: `docs/DDD_ARCHITECTURE.md`
