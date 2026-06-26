"""Resolve journey sources → graph node IDs + hierarchical output paths.

Also provides ``compute_journey_output_path`` for the hierarchical
``Language/Package/Class/Method`` output directory structure (Q2).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from md_generator.codeflow.graph.multigraph_utils import CodeflowGraph
from md_generator.codeflow.graph.query import GraphQuery
from md_generator.codeflow.journey.models import JourneyConfig, JourneyType


# Languages that have classes
_CLASS_LANGUAGES: frozenset[str] = frozenset({
    "java", "python", "javascript", "typescript", "tsx", "jsx",
    "csharp", "kotlin", "swift", "ruby", "rust", "php", "scala",
})


# ---------------------------------------------------------------------------
# Start-node resolution
# ---------------------------------------------------------------------------

def resolve_journey_starts(
    g: CodeflowGraph,
    query: GraphQuery,
    config: JourneyConfig,
    entry_ids: list[str],
    parse_results: list[Any] | None = None,
) -> list[str]:
    """Map journey config and entry hints to concrete graph node IDs.

    Priority order:
    1. Explicit ``entry_ids`` from ``--journey-entry``
    2. ``--journey-all-files`` → all file nodes
    3. ``--journey-all-classes`` → all class nodes
    4. ``--journey-all-methods`` → all method / function nodes
    5. ``--journey-all-entrypoints`` → all API / scheduler / queue / main nodes
    6. ``--journey-type`` based auto-resolution
    """
    if entry_ids:
        # Validate that they exist in the graph
        return [eid for eid in entry_ids if eid in g]

    if config.generate_all_files:
        return [d["id"] for d in query.find_nodes_by_kind("FILE")]

    if config.generate_all_classes:
        return [d["id"] for d in query.find_nodes_by_kind("CLASS")]

    if config.generate_all_methods:
        results = query.find_methods()
        return [d["id"] for d in results]

    if config.generate_all_entrypoints:
        starts: list[str] = []
        for kind in ("ENTRY", "API", "SCHEDULER", "QUEUE_CONSUMER", "EVENT_LISTENER", "CLI", "MAIN"):
            starts.extend(d["id"] for d in query.find_nodes_by_kind(kind))
        # Fallback: methods with in-degree 0 in call-only sub-graph
        if not starts:
            for d in query.find_methods():
                nid = d["id"]
                preds = list(g.predecessors(nid))
                if not preds:
                    starts.append(nid)
        return starts

    # Journey-type based resolution
    if config.journey_type == JourneyType.REPOSITORY:
        # Repository journey starts from all entry points
        return resolve_journey_starts(
            g, query,
            JourneyConfig(generate_all_entrypoints=True),
            [], parse_results,
        )

    if config.journey_type == JourneyType.DATABASE:
        return [d["id"] for d in query.find_tables()]

    if config.journey_type == JourneyType.CONFIG:
        return [d["id"] for d in query.find_config()]

    if config.journey_type == JourneyType.DEPENDENCY:
        return [d["id"] for d in query.find_dependencies()]

    # Default: use provided entry_ids (could be empty)
    return [eid for eid in entry_ids if eid in g]


def resolve_cross_repo_starts(
    g: CodeflowGraph,
    query: GraphQuery,
    config: JourneyConfig,
    multi_repo_labels: list[str],
) -> list[str]:
    """Resolve start nodes across multiple repositories in the merged graph.

    Returns node IDs from all repositories that match entry-point criteria.
    """
    starts: list[str] = []
    for n, d in g.nodes(data=True):
        repo_label = d.get("repository") or d.get("repo_label")
        if repo_label and repo_label in multi_repo_labels:
            node_type = (d.get("type") or d.get("kind") or "").upper()
            if node_type in ("ENTRY", "API", "SCHEDULER", "QUEUE_CONSUMER", "MAIN", "CLI"):
                starts.append(str(n))
    return starts


# ---------------------------------------------------------------------------
# Hierarchical output path (Q2)
# ---------------------------------------------------------------------------

def compute_journey_output_path(
    node_id: str,
    g: CodeflowGraph,
    journeys_root: Path,
) -> Path:
    """Compute hierarchical directory for a journey based on language, package, class, method.

    Examples::

        Java method:  journeys/Java/com/company/user/UserService/authenticate/
        Python func:  journeys/Python/app/services/UserService/authenticate/
        Go function:  journeys/Go/pkg/auth/authenticate/
        C function:   journeys/C/src/utils/parse_config/

    For languages without classes (Go, C, Lua) the path uses module/package path directly.
    """
    data: dict[str, Any] = dict(g.nodes[node_id]) if node_id in g else {}

    language = (data.get("language") or "unknown").capitalize()
    file_path = data.get("file_path") or ""
    class_name = data.get("class_name") or ""
    method_name = data.get("method_name") or data.get("name") or node_id

    # Build package path from file_path
    pp = PurePosixPath(file_path.replace("\\", "/"))
    parts_list: list[str] = list(pp.parts)
    # Remove the filename from the path
    if parts_list and "." in parts_list[-1]:
        parts_list = parts_list[:-1]
    # Remove leading drive / dot / src prefixes
    while parts_list and parts_list[0] in (".", "/", "src", "lib", "app"):
        parts_list = parts_list[1:]

    # Sanitise each part
    sanitised = [_sanitise_segment(p) for p in parts_list if p]

    path = journeys_root / language
    for seg in sanitised:
        path = path / seg

    lang_lower = (data.get("language") or "").lower()
    if lang_lower in _CLASS_LANGUAGES and class_name:
        path = path / _sanitise_segment(class_name)

    path = path / _sanitise_segment(method_name)

    return path


def _sanitise_segment(name: str) -> str:
    """Make a string safe for use as a directory name."""
    # Remove parentheses, angle brackets, etc.
    cleaned = name.replace("()", "").replace("(", "_").replace(")", "").replace("<", "_").replace(">", "")
    cleaned = cleaned.replace(":", "_").replace("*", "_").replace("?", "_").replace('"', "_")
    cleaned = cleaned.replace("|", "_").replace("\\", "/")
    # Collapse multiple underscores
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "unknown"
