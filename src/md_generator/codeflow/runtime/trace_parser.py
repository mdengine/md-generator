from __future__ import annotations

import json
from pathlib import Path

from md_generator.codeflow.enterprise_ir.runtime import RuntimeEntity, RuntimeEvent


class RuntimeTraceParser:
    def parse(self, trace_file: Path) -> list[RuntimeEntity]:
        """Parses a trace execution JSON payload and returns RuntimeEntity items."""
        entities: list[RuntimeEntity] = []
        if not trace_file.exists():
            return entities
        try:
            data = json.loads(trace_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    ent = RuntimeEntity(
                        id=f"runtime://{item.get('span_id', 'span')}",
                        metadata=None,  # type: ignore
                        trace_id=item.get("trace_id"),
                        span_id=item.get("span_id"),
                        parent_span_id=item.get("parent_span_id"),
                    )
                    entities.append(ent)
        except Exception:
            pass
        return entities
