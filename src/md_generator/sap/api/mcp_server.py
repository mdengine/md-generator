from __future__ import annotations

import os


def main() -> None:
    """Run sap-to-md API (MCP mount can be added when mdengine[mcp] is installed)."""
    import uvicorn

    host = os.environ.get("SAP_TO_MD_HOST", "127.0.0.1")
    port = int(os.environ.get("SAP_TO_MD_PORT", "8020"))
    uvicorn.run("md_generator.sap.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
