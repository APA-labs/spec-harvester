"""Storage adapters (raw bodies, manifests)."""

from spec_crawler.infrastructure.storage.manifest import should_save
from spec_crawler.infrastructure.storage.writer import SavedDocument, write_document

__all__ = ["SavedDocument", "write_document", "should_save"]
