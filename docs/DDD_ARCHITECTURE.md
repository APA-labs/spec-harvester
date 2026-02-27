# DDD-Oriented Package Layout

This project is organized around domain-first boundaries.

## Layers

- `src/spec_harvester/domain`
  - Pure domain concepts and rules.
  - Current modules: `policy.py`, `url.py`, `hashing.py`, `meta.py`.

- `src/spec_harvester/application`
  - Use cases and orchestration logic.
  - Current modules: `queue.py` (crawl orchestration flow).

- `src/spec_harvester/infrastructure`
  - External integrations and technical adapters.
  - `config/`: policy file loading (`policy_loader.py`, `policies/*.json`)
  - `http/`: networking concerns (`http_client.py`, `robots.py`, `rate_limit.py`)
  - `parsers/`: content parsing (`links.py`)
  - `storage/`: persistence adapters (`writer.py`, `manifest.py`)

- `src/spec_harvester/interfaces`
  - Entry points for users/systems.
  - Current module: CLI (`cli.py`).

## Compatibility Notes

- `spec_crawler` remains as a thin compatibility package for previous entrypoints.
- `spec_harvester` is the canonical package namespace.

## Dependency Direction

- `interfaces` -> `application` -> `domain`
- `infrastructure` can be used by `application`
- `domain` must not depend on `infrastructure` or `interfaces`
