from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileNode:
    path: Path
    relative_path: str
    suffix: str
    project_name: str | None = None
    module_name: str | None = None
    package_name: str | None = None


@dataclass
class PackageNode:
    name: str
    parent_name: str | None = None
    files: list[FileNode] = field(default_factory=list)
    subpackages: list[str] = field(default_factory=list)  # Package names


@dataclass
class ModuleNode:
    name: str
    parent_project: str | None = None
    packages: dict[str, PackageNode] = field(default_factory=dict)
    files: list[FileNode] = field(default_factory=list)


@dataclass
class ProjectNode:
    name: str
    path: Path
    modules: dict[str, ModuleNode] = field(default_factory=dict)
    packages: dict[str, PackageNode] = field(default_factory=dict)
    files: list[FileNode] = field(default_factory=list)


@dataclass
class Workspace:
    path: Path
    projects: dict[str, ProjectNode] = field(default_factory=dict)
    files: list[FileNode] = field(default_factory=list)


@dataclass
class Repository:
    name: str
    path: Path
    workspace: Workspace
    branch: str = "main"
    commit: str = "HEAD"
    fingerprint: str | None = None
