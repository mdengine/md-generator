from __future__ import annotations

import asyncio

import pytest

fastmcp = pytest.importorskip("fastmcp")


def test_mcp_server_defines_tools() -> None:
    from md_generator.word.api import mcp_server

    async def _names() -> set[str]:
        m = mcp_server.mcp
        if hasattr(m, "get_tools"):
            res = m.get_tools()
            if asyncio.iscoroutine(res):
                tools = await res
            else:
                tools = res
            if isinstance(tools, dict):
                return set(tools.keys())
            elif isinstance(tools, (list, set)):
                return {getattr(t, "name", str(t)) for t in tools}
        if hasattr(m, "_tool_manager") and hasattr(m._tool_manager, "_tools"):
            return set(m._tool_manager._tools.keys())
        if hasattr(m, "_tools"):
            return set(m._tools.keys())
        return set()

    found = asyncio.run(_names())
    assert "convert_docx_to_artifact_zip" in found
    assert "convert_docx_base64_to_artifact_zip" in found
