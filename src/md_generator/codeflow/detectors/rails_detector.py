"""Rails router DSL, engines, and ActionCable entry hints."""

from __future__ import annotations

import re
from pathlib import Path

from md_generator.codeflow.models.ir import EntryKind, EntryRecord
from md_generator.codeflow.parsers.treesitter_common import rel_key

_HTTP_VERB_ROUTE = re.compile(
    r"\b(get|post|put|patch|delete|head|options)\s+['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
_ROOT_ROUTE = re.compile(r"\broot\s+['\"]?(?:to\s*=>\s*)?['\"]?(\w+#\w+|\w+)", re.IGNORECASE)
_RESOURCES = re.compile(r"\bresources\s+:([\w]+)")
_RESOURCE = re.compile(r"\bresource\s+:([\w]+)")
_NAMESPACE = re.compile(r"\bnamespace\s+:([\w]+)")
_MOUNT_ENGINE = re.compile(r"\bmount\s+([\w:]+(?:::Engine)?)", re.IGNORECASE)
_ACTIONCABLE_CHANNEL = re.compile(
    r"class\s+(\w+)\s*<\s*(?:ApplicationCable::Channel|ActionCable::Channel::Base)",
    re.IGNORECASE,
)
_SUBSCRIBED_METHOD = re.compile(r"\bdef\s+(subscribed|receive|unsubscribed)\b")


def detect_rails_entries(path: Path, project_root: Path) -> list[EntryRecord]:
    if path.suffix.lower() != ".rb":
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    key = rel_key(path, project_root)
    fp = str(path.resolve())
    out: list[EntryRecord] = []
    seen: set[str] = set()

    def add(sid: str, label: str, line: int, *, kind: EntryKind = EntryKind.API_REST) -> None:
        if sid in seen:
            return
        seen.add(sid)
        out.append(
            EntryRecord(symbol_id=sid, kind=kind, label=label, file_path=fp, line=line),
        )

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        for m in _HTTP_VERB_ROUTE.finditer(line):
            verb, route_path = m.group(1).lower(), m.group(2)
            add(
                f"{key}::routes.{verb}.{route_path}",
                f"Rails route ({verb.upper()} {route_path})",
                i,
            )
        mroot = _ROOT_ROUTE.search(line)
        if mroot:
            add(f"{key}::routes.root.{mroot.group(1)}", "Rails root route", i)
        for m in _RESOURCES.finditer(line):
            add(f"{key}::routes.resources.{m.group(1)}", f"Rails resources :{m.group(1)}", i)
        for m in _RESOURCE.finditer(line):
            add(f"{key}::routes.resource.{m.group(1)}", f"Rails resource :{m.group(1)}", i)
        for m in _NAMESPACE.finditer(line):
            add(f"{key}::routes.namespace.{m.group(1)}", f"Rails namespace :{m.group(1)}", i)
        for m in _MOUNT_ENGINE.finditer(line):
            mount_target = m.group(1)
            add(f"{key}::routes.mount.{mount_target}", f"Rails mount {mount_target}", i)

    if _ACTIONCABLE_CHANNEL.search(text) and _SUBSCRIBED_METHOD.search(text):
        ch = _ACTIONCABLE_CHANNEL.search(text)
        cname = ch.group(1) if ch else "Channel"
        line_no = text[: ch.start()].count("\n") + 1 if ch else 1
        for m in _SUBSCRIBED_METHOD.finditer(text):
            mname = m.group(1)
            add(
                f"{key}::{cname}.{mname}",
                f"ActionCable {mname}",
                text[: m.start()].count("\n") + 1,
                kind=EntryKind.QUEUE,
            )
        if not any(e.symbol_id.endswith(".subscribed") for e in out):
            add(
                f"{key}::{cname}.subscribed",
                "ActionCable channel",
                line_no,
                kind=EntryKind.QUEUE,
            )

    return out
