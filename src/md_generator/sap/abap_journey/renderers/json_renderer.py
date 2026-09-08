from __future__ import annotations

import json
from md_generator.sap.abap_journey.models import CallGraph

class JsonRenderer:
    @staticmethod
    def render(graph: CallGraph) -> str:
        return json.dumps(graph.to_dict(), indent=2)
