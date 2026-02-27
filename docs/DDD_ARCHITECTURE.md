# DDD-Oriented Package Layout

This project is organized around domain-first boundaries.

## Layers

- `src/spec_crawler/domain`
  - Pure domain concepts and rules.
  - Current modules: `policy.py`, `url.py`, `hashing.py`, `meta.py`.

- `src/spec_crawler/application`
  - Use cases and orchestration logic.
  - Current modules: `queue.py` (placeholder for crawl flow coordination).

- `src/spec_crawler/infrastructure`
  - External integrations and technical adapters.
  - `config/`: policy file loading (`policy_loader.py`, `policies/*.json`)
  - `http/`: networking concerns (`http_client.py`, `robots.py`, `rate_limit.py`)
  - `parsers/`: content parsing (`links.py`)
  - `storage/`: persistence adapters (`writer.py`, `manifest.py`)

- `src/spec_crawler/interfaces`
  - Entry points for users/systems.
  - Current module: CLI (`cli.py`).

## Compatibility Notes

- `spec_crawler.cli` remains as a thin wrapper to keep existing command entrypoints stable.
- `spec_crawler.config` and `spec_crawler.core` re-export public APIs from the new layer layout.

## Dependency Direction

- `interfaces` -> `application` -> `domain`
- `infrastructure` can be used by `application`
- `domain` must not depend on `infrastructure` or `interfaces`
