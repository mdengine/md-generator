from __future__ import annotations

from typing import Any, Iterator

try:
    from lxml import etree
except ImportError:  # pragma: no cover
    etree = None  # type: ignore[assignment]


def iterparse_events(path: str, tag_names: set[str]) -> Iterator[tuple[str, Any]]:
    if etree is None:
        raise ImportError("lxml is required for HANA XML streaming; install mdengine[sap]")
    context = etree.iterparse(path, events=("end",), huge_tree=True)
    for _event, elem in context:
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local in tag_names:
            yield local, elem
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]


def local_tag(elem: Any) -> str:
    tag = getattr(elem, "tag", "")
    if not isinstance(tag, str):
        return str(tag)
    return tag.split("}")[-1] if "}" in tag else tag


def text(elem: Any, child: str, default: str = "") -> str:
    attr_val = elem.get(child)
    if attr_val:
        return str(attr_val).strip()
    for c in elem:
        if local_tag(c) == child:
            return (c.text or "").strip()
    return default
