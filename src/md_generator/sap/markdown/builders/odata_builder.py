"""Re-export from shared OData catalog writer."""

from md_generator.odata.writers.catalog_writer import (
    _render_entity_set,
    render_odata_catalog,
    write_text,
)

__all__ = ["render_odata_catalog", "write_text", "_render_entity_set"]
