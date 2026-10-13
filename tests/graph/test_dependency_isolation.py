import subprocess
import sys
import pytest

from md_generator.graph.exceptions import (
    GraphError,
    Neo4jDependencyError,
    GraphStoreError,
    GraphQueryError,
    TenantBoundaryError,
)
from md_generator.vector.exceptions import VectorError
from md_generator.adapters.crewai.exceptions import CrewAIAdapterError


def test_subprocess_core_import_isolation():
    """Verify that importing core md_generator modules does NOT leak neo4j into sys.modules."""
    code = (
        "import sys\n"
        "import md_generator.pipeline\n"
        "import md_generator.semantic\n"
        "import md_generator.vector\n"
        "leaked = [m for m in sys.modules if 'neo4j' in m]\n"
        "if leaked:\n"
        "    print(f'LEAK: {leaked}')\n"
        "    sys.exit(1)\n"
        "sys.exit(0)\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, f"Leaked neo4j modules: {result.stdout} {result.stderr}"


def test_exception_hierarchy_uncoupled():
    assert issubclass(Neo4jDependencyError, GraphError)
    assert issubclass(Neo4jDependencyError, ImportError)
    assert issubclass(GraphStoreError, GraphError)
    assert issubclass(GraphQueryError, GraphError)

    # GraphError is not VectorError or CrewAIAdapterError
    assert not issubclass(GraphError, VectorError)
    assert not issubclass(GraphError, CrewAIAdapterError)
    assert not issubclass(VectorError, GraphError)
    assert not issubclass(CrewAIAdapterError, GraphError)
