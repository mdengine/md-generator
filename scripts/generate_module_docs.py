#!/usr/bin/env python3
"""Generate enriched module documentation from src/md_generator source code."""

from __future__ import annotations

import argparse
import ast
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/vishal7090/md-generator/blob/main"
SRC = ROOT / "src" / "md_generator"
DOCS = ROOT / "docs" / "modules"
REF_API = ROOT / "docs" / "reference" / "api"
MKDOCS = ROOT / "mkdocs.yml"

ENRICH_MARKER = "## Implementation details (auto-enriched)"
GENERIC_THRESHOLD_LINES = 45

PAGE_FILES = [
    "overview.md",
    "responsibilities.md",
    "installation.md",
    "configuration.md",
    "workflows.md",
    "api.md",
    "database.md",
    "exceptions.md",
    "logging.md",
    "testing.md",
    "deployment.md",
    "lld.md",
    "parameters.md",
    "usecases.md",
    "architecture.md",
    "lifecycle.md",
    "sequence-diagrams.md",
    "extension-points.md",
    "performance.md",
    "security.md",
    "troubleshooting.md",
    "examples.md",
    "cli-reference.md",
    "integration.md",
    "compatibility.md",
    "best-practices.md",
    "developer-guide.md",
]

NAV_GROUPS: list[tuple[str, list[str]]] = [
    ("Overview", ["overview.md", "responsibilities.md"]),
    ("Setup", ["installation.md", "configuration.md", "compatibility.md"]),
    ("Usage", ["workflows.md", "usecases.md", "examples.md", "cli-reference.md"]),
    (
        "Technical",
        [
            "architecture.md",
            "lifecycle.md",
            "sequence-diagrams.md",
            "lld.md",
            "extension-points.md",
        ],
    ),
    ("Reference", ["parameters.md", "api.md", "integration.md"]),
    (
        "Operations",
        [
            "performance.md",
            "security.md",
            "troubleshooting.md",
            "deployment.md",
            "logging.md",
            "exceptions.md",
            "testing.md",
        ],
    ),
    ("Development", ["developer-guide.md", "best-practices.md", "database.md"]),
]


@dataclass
class CliArg:
    names: list[str]
    arg_type: str
    default: str
    required: str
    choices: str
    help: str
    metavar: str = ""


@dataclass
class ApiRoute:
    method: str
    path: str


@dataclass
class EnvVar:
    name: str
    default: str
    description: str


@dataclass
class ModuleSpec:
    key: str
    title: str
    package: str
    src_rel: str
    cli: str
    extra: str
    cli_alt: str = ""
    api_title: str = ""
    service: str = ""
    input_desc: str = ""
    output_desc: str = ""
    tier: str = "medium"
    has_db: bool = False
    has_jobs: bool = False
    has_mcp: bool = True
    test_dir: str = ""
    readme_link: str = ""
    deep_docs: list[str] = field(default_factory=list)
    entry_functions: list[str] = field(default_factory=list)
    extension_notes: str = ""
    integration_items: list[str] = field(default_factory=list)


MODULES: list[ModuleSpec] = [
    ModuleSpec("pdf", "PDF", "md_generator.pdf", "pdf", "md-pdf", extra="pdf", api_title="pdf-to-md", service="pdf-to-md",
               input_desc="PDF documents", output_desc="Markdown with optional artifact layout and extracted images",
               tier="simple", test_dir="pdf-to-md/tests", readme_link="pdf-to-md/README.md",
               entry_functions=["convert_pdf", "convert_pdf_to_artifact_dir", "ConvertOptions"],
               integration_items=["PyMuPDF", "pdfplumber", "optional Tesseract OCR"]),
    ModuleSpec("word", "Word", "md_generator.word", "word", "md-word", extra="word", api_title="word-to-md", service="word-to-md",
               input_desc="DOCX documents", output_desc="Markdown with optional embedded images",
               tier="simple", test_dir="word-to-md/tests", readme_link="word-to-md/README.md",
               entry_functions=["convert_docx_to_markdown", "WordToMdSettings"],
               integration_items=["mammoth", "markdownify"]),
    ModuleSpec("ppt", "PowerPoint", "md_generator.ppt", "ppt", "md-ppt", extra="ppt", api_title="ppt-to-md", service="ppt-to-md",
               input_desc="PPTX slide decks", output_desc="Slide Markdown and extracted assets",
               tier="medium", test_dir="ppt-to-md/tests", readme_link="ppt-to-md/README.md",
               entry_functions=["convert_pptx", "ConvertOptions", "build_artifact_zip_bytes"],
               integration_items=["python-pptx", "embedded PDF/Word fallbacks", "OCR for images"]),
    ModuleSpec("xlsx", "Excel and CSV", "md_generator.xlsx", "xlsx", "md-xlsx", extra="xlsx", api_title="xlsx-to-md", service="xlsx-to-md",
               input_desc="XLSX, XLSM, CSV", output_desc="Worksheet or CSV Markdown tables",
               tier="simple", test_dir="xlsx-to-md/tests", readme_link="xlsx-to-md/README.md",
               entry_functions=["convert_excel_to_markdown", "ConvertConfig"],
               integration_items=["openpyxl"]),
    ModuleSpec("image", "Image OCR", "md_generator.image", "image", "md-image", extra="image or image-ocr", api_title="image-to-md", service="image-to-md",
               input_desc="Image files or directories", output_desc="OCR Markdown and metadata",
               tier="medium", test_dir="image-to-md/tests", readme_link="image-to-md/README.md",
               entry_functions=["convert_images", "convert_images_recursive", "build_backends"],
               extension_notes="OCR backends under `image/backends/` (tesseract, paddle, easy).",
               integration_items=["Pillow", "pytesseract", "paddleocr", "easyocr"]),
    ModuleSpec("text", "Text JSON XML", "md_generator.text", "text", "md-text", extra="text", api_title="txt-json-xml-to-md", service="txt-json-xml-to-md",
               input_desc="TXT, JSON, XML", output_desc="Readable Markdown representations",
               tier="simple", test_dir="txt-json-xml-to-md/tests", readme_link="txt-json-xml-to-md/README.md",
               entry_functions=["convert_text_file", "json_to_markdown", "xml_to_markdown", "detect_format"],
               integration_items=["xmltodict", "lxml"]),
    ModuleSpec("archive", "ZIP Archive", "md_generator.archive", "archive", "md-zip", extra="archive plus nested format extras", api_title="zip-to-md", service="zip-to-md",
               input_desc="ZIP archives", output_desc="Directory-oriented Markdown bundle",
               tier="medium", test_dir="zip-to-md/tests", readme_link="zip-to-md/README.md",
               entry_functions=["convert_archive", "convert_zip", "extract_archive"],
               integration_items=["nested pdf/word/ppt/xlsx/image converters"]),
    ModuleSpec("url", "URL and Web", "md_generator.url", "url", "md-url", extra="url or url-full", api_title="url-to-md", service="url-to-md",
               input_desc="HTTP(S) pages", output_desc="Cleaned Markdown and optional artifacts",
               tier="medium", test_dir="url-to-md/tests", readme_link="url-to-md/README.md",
               entry_functions=["convert_url", "run_crawl", "convert_one_page_artifact"],
               integration_items=["httpx", "readability-lxml", "markdownify", "robots.txt"]),
    ModuleSpec("media-audio", "Audio", "md_generator.media.audio", "media/audio", "md-audio", extra="audio", api_title="audio-to-md", service="audio-to-md",
               input_desc="Audio files", output_desc="Whisper transcript Markdown",
               tier="medium", test_dir="audio-to-md/tests", readme_link="audio-to-md/README.md",
               entry_functions=["DocumentConverter", "AudioConverter"],
               integration_items=["openai-whisper", "imageio-ffmpeg"]),
    ModuleSpec("media-video", "Video", "md_generator.media.video", "media/video", "md-video", extra="video", api_title="video-to-md", service="video-to-md",
               input_desc="Video files", output_desc="Transcript Markdown with video metadata",
               tier="medium", test_dir="video-to-md/tests", readme_link="video-to-md/README.md",
               entry_functions=["VideoToMarkdownService", "video_probe_from_ffprobe"],
               integration_items=["ffmpeg via imageio-ffmpeg", "Whisper"]),
    ModuleSpec("media-youtube", "YouTube", "md_generator.media.youtube", "media/youtube", "md-youtube", extra="youtube", api_title="youtube-to-md", service="youtube-to-md",
               input_desc="YouTube URLs", output_desc="Transcript and metadata Markdown",
               tier="simple", test_dir="youtube-to-md/tests", readme_link="youtube-to-md/README.md",
               entry_functions=["YouTubeToMarkdownService", "YouTubeConverter"],
               integration_items=["youtube-transcript-api", "httpx"]),
    ModuleSpec("playwright", "Playwright Web Capture", "md_generator.playwright", "playwright", "md-playwright", extra="playwright", api_title="playwright-to-md", service="playwright-to-md",
               input_desc="Rendered web pages and SPAs", output_desc="Browser-captured Markdown",
               tier="medium", test_dir="playwright-to-md/tests", readme_link="playwright-to-md/README.md",
               entry_functions=["convert_url_to_md", "PlaywrightOptions"],
               integration_items=["playwright", "Chromium browser binaries"]),
    ModuleSpec("db", "Database Metadata", "md_generator.db", "db", "md-db", cli_alt="mdengine db-to-md", extra="db", api_title="db-to-md", service="db-to-md",
               input_desc="Postgres, MySQL, Oracle, SQLite, Mongo, Access", output_desc="Schema docs, ERD, Markdown ZIP",
               tier="complex", has_db=True, has_jobs=True, test_dir="db-to-md/tests", readme_link="db-to-md/README.md",
               entry_functions=["extract_to_markdown", "create_adapter", "RunConfig", "JobManager"],
               extension_notes="Database adapters in `db/adapters/` (factory pattern).",
               integration_items=["SQLAlchemy", "psycopg2", "pymysql", "oracledb", "pymongo", "Graphviz", "mermaid-py"]),
    ModuleSpec("graph", "Graph Metadata", "md_generator.graph", "graph", "md-graph", cli_alt="mdengine graph-to-md", extra="graph", api_title="graph-to-md", service="graph-to-md",
               input_desc="Neo4j or NetworkX GraphML/GML", output_desc="Node/relationship Markdown, Mermaid, Graphviz",
               tier="medium", has_db=True, has_jobs=True, test_dir="graph-to-md/tests", readme_link="graph-to-md/README.md",
               entry_functions=["extract_to_markdown", "Neo4jAdapter", "GraphRunConfig"],
               extension_notes="Graph adapters: `graph/adapters/neo4j_adapter.py`, `networkx_adapter.py`.",
               integration_items=["neo4j", "networkx", "Graphviz"]),
    ModuleSpec("openapi", "OpenAPI", "md_generator.openapi", "openapi", "md-openapi", cli_alt="mdengine openapi-to-md generate", extra="openapi", api_title="openapi-to-md", service="openapi-to-md",
               input_desc="OpenAPI 3.x or Swagger 2.0", output_desc="API documentation ZIP bundle",
               tier="medium", has_jobs=False, test_dir="openapi-to-md/tests", readme_link="openapi-to-md/README.md",
               entry_functions=["extract_to_markdown", "load_spec", "swagger2_to_openapi3"],
               extension_notes="Pipeline: loaders, parsers, resolvers, generators, writers.",
               integration_items=["prance", "openapi-spec-validator", "pyyaml"]),
    ModuleSpec("codeflow", "Codeflow", "md_generator.codeflow", "codeflow", "md-codeflow", cli_alt="codeflow / mdengine codeflow-to-md scan", extra="codeflow", api_title="codeflow-to-md", service="codeflow-to-md",
               input_desc="Source repositories", output_desc="Architecture Markdown, graphs, flow docs, JSON, Mermaid",
               tier="complex", has_jobs=True, test_dir="codeflow-to-md/tests", readme_link="codeflow-to-md/README.md",
               deep_docs=["codeflow-to-md/docs/graph-and-outputs.md", "codeflow-to-md/docs/remote-repos.md", "codeflow-to-md/docs/cache-and-semantic.md"],
               entry_functions=["run_scan", "ScanConfig", "build_output_zip", "build_graph"],
               extension_notes="Language parsers under `codeflow/parsers/` and optional tree-sitter adapters.",
               integration_items=["networkx", "javalang", "optional Celery/Redis workers", "sentence-transformers for semantic"]),
    ModuleSpec("log", "Log Analysis", "md_generator.log", "log", "md-log", cli_alt="mdengine log-to-md", extra="log", api_title="log-to-md", service="log-to-md",
               input_desc="Log files and uploads", output_desc="Parsed events, summaries, incidents, optional clustering",
               tier="complex", has_jobs=True, test_dir="log-to-md/tests", readme_link="log-to-md/README.md",
               entry_functions=["extract_to_markdown", "run_pipeline", "LogRunConfig", "load_run_config"],
               extension_notes="Presets in `log/config/presets/`; pipeline stages under ingestion, parsing, clustering.",
               integration_items=["pandas", "scikit-learn", "optional sentence-transformers", "Chroma export"]),
    ModuleSpec("tools-assistant", "AI Assistant Tools", "md_generator.tools.assistant", "tools/assistant", "mdengine ai assist", cli_alt="mdengine ai export", extra="skill-openai or skill-rag-chroma", api_title="(none)", service="tool-assistant",
               input_desc="Skill bundles and prompts", output_desc="Assembled context and assistant output", tier="medium", has_mcp=False, has_jobs=False,
               test_dir="tool-assistant/tests", readme_link="ai/README.md",
               entry_functions=["Registry", "MasterAgent", "run_assist", "run_export"],
               integration_items=["OpenAI optional", "Chroma RAG optional"]),
    ModuleSpec("tools-skill-builder", "Skill Builder", "md_generator.tools.skill_builder", "tools/skill_builder", "mdengine skill build", extra="(base package)", api_title="(none)", service="tool-skill-builder",
               input_desc="Project metadata", output_desc="Structured skills under ai/", tier="medium", has_mcp=False, has_jobs=False,
               test_dir="", readme_link="ai/README.md",
               entry_functions=["run_generate", "build_dependency_graph", "build_routing_block"],
               integration_items=["pyproject.toml scripts", "git diff for --since"]),
]


def module_src(spec: ModuleSpec) -> Path:
    return SRC / spec.src_rel.replace("/", "\\") if "\\" in spec.src_rel else SRC / spec.src_rel


def list_py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def repo_link(rel_path: str) -> str:
    rel = rel_path.replace("\\", "/").lstrip("/")
    return f"{REPO_URL}/{rel}"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def find_cli_files(spec: ModuleSpec) -> list[Path]:
    root = module_src(spec)
    candidates = [
        root / "converter.py",
        root / "cli.py",
        root / "cli" / "main.py",
    ]
    return [p for p in candidates if p.exists()]


def find_api_file(spec: ModuleSpec) -> Path | None:
    root = module_src(spec)
    for rel in ("api/main.py", "api/app.py"):
        p = root / rel
        if p.exists():
            return p
    return None


def find_settings_files(spec: ModuleSpec) -> list[Path]:
    root = module_src(spec)
    paths = list(root.glob("**/settings.py"))
    paths.extend(root.glob("**/options.py"))
    return sorted(set(paths))[:8]


def find_yaml_configs(spec: ModuleSpec) -> list[Path]:
    root = module_src(spec)
    configs = []
    for name in ("default.yaml", "codeflow.yaml"):
        p = root / "config" / name
        if p.exists():
            configs.append(p)
    presets = root / "config" / "presets"
    if presets.exists():
        configs.extend(sorted(presets.glob("*.yaml"))[:6])
    return configs


def ast_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def extract_cli_args(path: Path) -> list[CliArg]:
    text = read_text(path)
    if not text:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    args: list[CliArg] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "add_argument":
                names: list[str] = []
                arg_type = "str"
                default = "—"
                required = "optional"
                choices = "—"
                help_text = ""
                metavar = ""
                if node.args:
                    first = node.args[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        names.append(first.value)
                    elif isinstance(first, ast.Tuple):
                        names = [
                            elt.value
                            for elt in first.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        ]
                for kw in node.keywords:
                    if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                        help_text = str(kw.value.value)
                    elif kw.arg == "default":
                        default = ast_unparse(kw.value) or default
                    elif kw.arg == "choices":
                        choices = ast_unparse(kw.value)
                    elif kw.arg == "type":
                        arg_type = ast_unparse(kw.value)
                    elif kw.arg == "metavar":
                        metavar = ast_unparse(kw.value)
                    elif kw.arg == "action" and isinstance(kw.value, ast.Constant):
                        if kw.value.value == "store_true":
                            arg_type = "flag"
                            default = "false"
                if any(n.startswith("-") for n in names):
                    required = "optional"
                elif names:
                    required = "required"
                args.append(
                    CliArg(
                        names=names or ["(positional)"],
                        arg_type=arg_type,
                        default=default,
                        required=required,
                        choices=choices,
                        help=help_text,
                        metavar=metavar,
                    )
                )
            self.generic_visit(node)

    Visitor().visit(tree)
    return args


def extract_routes(path: Path) -> list[ApiRoute]:
    text = read_text(path)
    routes = []
    for m in re.finditer(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', text):
        routes.append(ApiRoute(method=m.group(1).upper(), path=m.group(2)))
    return routes


def extract_env_vars(paths: list[Path], prefix_hint: str) -> list[EnvVar]:
    envs: list[EnvVar] = []
    seen: set[str] = set()
    for path in paths:
        text = read_text(path)
        for m in re.finditer(r'os\.environ\.get\(\s*["\']([A-Z0-9_]+)["\']', text):
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                envs.append(EnvVar(name, "—", f"From `{path.relative_to(ROOT)}`"))
        for m in re.finditer(r'f"([A-Z][A-Z0-9_]*)_\{name\}"', text):
            base = m.group(1)
            for suffix in ("MAX_UPLOAD_MB", "MAX_SYNC_UPLOAD_MB", "JOB_TTL_SECONDS", "TEMP_DIR", "CORS_ORIGINS", "PORT"):
                full = f"{base}_{suffix}"
                if full not in seen:
                    seen.add(full)
                    envs.append(EnvVar(full, "—", f"Derived env pattern in `{path.name}`"))
        for m in re.finditer(r'([A-Z][A-Z0-9_]+_PORT)', text):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                envs.append(EnvVar(m.group(1), "—", "Service port override"))
    if prefix_hint and not envs:
        envs.append(EnvVar(f"{prefix_hint}_PORT", "varies", "HTTP API listen port"))
    return envs


def extract_dataclass_fields(root: Path) -> list[tuple[str, str, str]]:
    fields: list[tuple[str, str, str]] = []
    for py in list_py_files(root)[:40]:
        text = read_text(py)
        if "@dataclass" not in text and "BaseModel" not in text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "Options" not in node.name and "Config" not in node.name and "Settings" not in node.name:
                    continue
                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                        fields.append((node.name, stmt.target.id, ast_unparse(stmt.annotation)))
    return fields[:40]


def is_generic_content(text: str) -> bool:
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    if len(lines) <= GENERIC_THRESHOLD_LINES:
        return True
    if "participates in the unified `mdengine` distribution" in text:
        return True
    return False


def merge_write(path: Path, new_content: str, *, force: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        old = read_text(path)
        if old.strip() and not is_generic_content(old) and ENRICH_MARKER not in old:
            if ENRICH_MARKER in new_content:
                return
            merged = old.rstrip() + "\n\n" + ENRICH_MARKER + "\n\n" + new_content.split("\n", 1)[-1] if "\n" in new_content else new_content
            path.write_text(merged, encoding="utf-8")
            return
    path.write_text(new_content, encoding="utf-8")


def table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_No entries detected._\n"
    line = "| " + " | ".join(headers) + " |\n"
    sep = "| " + " | ".join("---" for _ in headers) + " |\n"
    body = "".join("| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |\n" for row in rows)
    return line + sep + body


def cli_arg_rows(args: list[CliArg]) -> list[list[str]]:
    rows = []
    for a in args:
        name = ", ".join(f"`{n}`" for n in a.names)
        rows.append([name, a.arg_type, a.required, a.default, a.choices, a.help or "—"])
    return rows


@dataclass
class ModuleContext:
    spec: ModuleSpec
    cli_args: list[CliArg]
    routes: list[ApiRoute]
    env_vars: list[EnvVar]
    py_files: list[Path]
    dataclass_fields: list[tuple[str, str, str]]
    yaml_configs: list[Path]
    api_path: Path | None
    cli_paths: list[Path]


def build_context(spec: ModuleSpec) -> ModuleContext:
    root = module_src(spec)
    cli_paths = find_cli_files(spec)
    cli_args: list[CliArg] = []
    for p in cli_paths:
        cli_args.extend(extract_cli_args(p))
    if spec.key == "tools-assistant":
        cli_path = SRC / "tools" / "assistant" / "cli.py"
        if cli_path.exists():
            cli_args.extend(extract_cli_args(cli_path))
    if spec.key == "tools-skill-builder":
        cli_path = SRC / "tools" / "skill_builder" / "__main__.py"
        if cli_path.exists():
            cli_args.extend(extract_cli_args(cli_path))
    api_path = find_api_file(spec)
    routes = extract_routes(api_path) if api_path else []
    prefix = spec.api_title.upper().replace("-", "_") if spec.api_title and spec.api_title != "(none)" else ""
    env_vars = extract_env_vars(find_settings_files(spec), prefix)
    return ModuleContext(
        spec=spec,
        cli_args=cli_args,
        routes=routes,
        env_vars=env_vars,
        py_files=list_py_files(root),
        dataclass_fields=extract_dataclass_fields(root),
        yaml_configs=find_yaml_configs(spec),
        api_path=api_path,
        cli_paths=cli_paths,
    )


def gen_overview(ctx: ModuleContext) -> str:
    s = ctx.spec
    rel = s.src_rel
    alt = f"\n- Alternate entry: `{s.cli_alt}`" if s.cli_alt else ""
    deep = "\n".join(f"- [{Path(d).name}]({repo_link(d)})" for d in s.deep_docs) if s.deep_docs else ""
    deep_block = f"\n## Deep documentation\n\n{deep}\n" if deep else ""
    return f"""# {s.title} Module Overview

## Purpose

The **{s.title}** module (`{s.package}`) converts **{s.input_desc}** into **{s.output_desc}**. It exists so teams can publish searchable, diff-friendly Markdown from operational inputs without maintaining separate documentation pipelines per format.

## Problem solved

- Manual copy/paste from {s.input_desc} into wikis does not scale.
- Downstream AI/RAG workflows need stable text and asset bundles.
- CI and gateways need a consistent CLI/API surface across `mdengine` modules.

## When to use

- You need repeatable Markdown export from {s.input_desc}.
- You want CLI automation, HTTP conversion, or MCP tool integration (where implemented).
- You can install the `{s.extra}` optional extra (and `api` for HTTP services).

## When not to use

- Inputs fall outside supported formats or size limits enforced by the module.
- You require authenticated multi-tenant SaaS features (not provided by this module; use gateway auth).
- You need transactional writes into application databases (this module documents or transforms; it does not own app schemas except metadata export modules).

## Package facts

| Item | Value |
|------|-------|
| Import path | `{s.package}` |
| Source tree | `src/md_generator/{rel}` |
| CLI | `{s.cli}` |{alt}
| PyPI extra | `{s.extra}` |
| Complexity tier | `{s.tier}` |
| API service name | `{s.api_title or "N/A"}` |

## Primary entry points

{chr(10).join(f"- `{fn}`" for fn in s.entry_functions) or "- See source package for public callables."}

```mermaid
flowchart LR
    Input[Input] --> Validate[Validate]
    Validate --> Core[{s.key}_core]
    Core --> Markdown[Markdown_output]
    Core --> Assets[Optional_assets]
```

{deep_block}
"""


def gen_parameters(ctx: ModuleContext) -> str:
    s = ctx.spec
    cli_rows = cli_arg_rows(ctx.cli_args)
    env_rows = [[e.name, "string/int", "optional", e.default, "—", e.description] for e in ctx.env_vars]
    dc_rows = [[c, f, t, "varies", "—", f"Field on options/config class"] for c, f, t in ctx.dataclass_fields]
    route_rows = [[r.method, r.path, "HTTP", "—", "—", "FastAPI route"] for r in ctx.routes]
    yaml_rows = [[str(p.relative_to(ROOT)), "YAML", "optional", "—", "—", "Packaged or preset config"] for p in ctx.yaml_configs]
    return f"""# {s.title} Parameter Reference

All parameters below are extracted from source where possible. Validate against `--help` and OpenAPI (`/docs`) before production use.

## CLI parameters

{table(["Name", "Type", "Required", "Default", "Choices", "Description"], cli_rows)}

## API routes (HTTP parameters)

{table(["Method", "Path", "Type", "Required", "Default", "Description"], route_rows)}

## Environment variables

{table(["Name", "Type", "Required", "Default", "Choices", "Description"], env_rows)}

## Config file parameters

{table(["File", "Type", "Required", "Default", "Choices", "Description"], yaml_rows)}

## Options / dataclass fields (sample)

{table(["Class", "Field", "Type", "Required", "Default", "Description"], dc_rows)}

## Validation and edge cases

- Positional CLI arguments are required unless documented as optional flags.
- Upload APIs enforce size limits via environment variables (413 on exceed).
- Missing optional dependencies raise install-time or runtime errors referencing the PyPI extra `{s.extra}`.
"""


def gen_usecases(ctx: ModuleContext) -> str:
    s = ctx.spec
    cases = [
        ("Local developer conversion", f"Convert a single {s.input_desc} during feature work.", f"Sample {s.input_desc}", s.output_desc, f"`pip install -e \".[{s.extra.split()[0]}]\"`", "Fast for small inputs; use job API for large bundles."),
        ("CI documentation artifact", "Publish Markdown into build artifacts for review.", "Tracked input files", "Artifact directory or ZIP", "CLI in pipeline + cache extras", "Pin extras in CI image; cache Whisper/browser deps separately for media modules."),
        ("Gateway HTTP service", "Expose conversion behind nginx path prefix.", "Multipart upload or JSON body", "ZIP or JSON status", "`api` extra + Docker", "Set upload limits and timeouts at gateway."),
        ("Batch directory processing", "Process many files overnight.", "Directory tree", "Per-file output folders", "Shell loop or job endpoints", "Disk space and temp job TTL matter."),
        ("AI/RAG ingestion", "Feed Markdown into embeddings index.", s.output_desc, "Chunked Markdown", "Stable naming + front matter if enabled", "Sanitize secrets before indexing."),
    ]
    blocks = []
    for title, obj, inp, out, cfg, perf in cases:
        blocks.append(f"""### {title}

| Aspect | Detail |
|--------|--------|
| Objective | {obj} |
| Input | {inp} |
| Output | {out} |
| Configuration | {cfg} |
| Performance | {perf} |
| Failure | Missing extra, invalid input, timeout, upload too large |
| Recovery | Fix input; retry with job endpoint; increase limits via env |
""")
    return f"# {s.title} Use Cases\n\n" + "\n".join(blocks)


def gen_workflows(ctx: ModuleContext) -> str:
    s = ctx.spec
    job = "job workspace + download" if ctx.routes and any("job" in r.path for r in ctx.routes) else "direct response"
    return f"""# {s.title} Workflows

## CLI workflow

1. Install `mdengine[{s.extra.split()[0]}]`.
2. Run `{s.cli} --help` to list flags.
3. Provide input ({s.input_desc}) and output path.
4. Inspect generated Markdown and sidecar assets.

## API workflow

1. Install `mdengine[{s.extra.split()[0]},api]`.
2. Start uvicorn on `{s.package}` API module (see Deployment).
3. Call sync endpoint for small payloads or job endpoint for large conversions.
4. Poll job status and download artifact when complete.

## Processing pipeline

```mermaid
flowchart TD
    Start[Start] --> InputLoad[Load_input]
    InputLoad --> Validate[Validate_options]
    Validate --> Transform[Core_conversion]
    Transform --> Render[Render_Markdown]
    Render --> Package[Write_output_or_ZIP]
    Package --> End[Complete]
```

## Async job flow

Where job routes exist, background work uses in-process threads or domain job managers; results land in {job}.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Worker
    participant Storage
    Client->>API: POST job
    API->>Storage: create workspace
    API->>Worker: enqueue
    API-->>Client: job_id
    Worker->>Storage: write artifacts
    Client->>API: GET status/download
    API-->>Client: ZIP or Markdown
```
"""


def gen_architecture(ctx: ModuleContext) -> str:
    s = ctx.spec
    subpackages = sorted({p.parent.relative_to(module_src(s)).parts[0] for p in ctx.py_files if p.parent != module_src(s) and p.parent.relative_to(module_src(s)).parts})
    subs = ", ".join(f"`{x}`" for x in subpackages[:15]) or "`(package root)`"
    return f"""# {s.title} Architecture

## Internal layout

Source root: `src/md_generator/{s.src_rel}` ({len(ctx.py_files)} Python modules detected).

Subpackages and areas: {subs}.

## Component diagram

```mermaid
flowchart TB
    CLI[CLI_{s.cli}] --> Core[Core_engine]
    API[FastAPI_optional] --> Core
    Core --> Writers[Markdown_writers]
    Core --> Assets[Asset_handlers]
    Core --> Integrations[External_libraries]
```

## Dependency graph (logical)

- **Inputs:** {s.input_desc}
- **Outputs:** {s.output_desc}
- **Optional extras:** `{s.extra}` from `pyproject.toml`
- **Cross-module:** See `integration.md` for delegated converters and shared job patterns.

## Threading and async

- CLI runs synchronously in the invoking process.
- FastAPI routes may use background tasks or threads for long jobs.
- Domain modules (`db`, `graph`, `log`, `codeflow`) expose SSE/event streams for progress.

## Data flow

```mermaid
flowchart LR
    Raw[Raw_input] --> Parse[Parse_or_load]
    Parse --> Model[Internal_representation]
    Model --> Emit[Markdown_emitter]
    Emit --> Out[Files_or_ZIP]
```
"""


def gen_api(ctx: ModuleContext) -> str:
    s = ctx.spec
    if not ctx.routes:
        return f"""# {s.title} API

No FastAPI application was detected under `src/md_generator/{s.src_rel}/api/`.

## CLI-only module

Use `{s.cli}` or `{s.cli_alt or "mdengine subcommand"}` for all operations.

## MCP

{"MCP may still be available via other entrypoints; check package `mcp_server.py` files." if s.has_mcp else "No MCP server detected for this module."}
"""
    rows = [[r.method, r.path, "See OpenAPI `/docs`", "Upload/body per route", "Job id or ZIP", "Standard FastAPI errors"] for r in ctx.routes]
    mcp = "Many converter APIs mount MCP at `/mcp` when `mcp` extra is installed." if s.has_mcp else ""
    return f"""# {s.title} API

Service title: **{s.api_title}**  
Source: `{ctx.api_path.relative_to(ROOT) if ctx.api_path else "N/A"}`

## Endpoints

{table(["Method", "Path", "Auth", "Request", "Response", "Errors"], rows)}

## Sync vs async

- **Sync routes** return artifacts immediately (subject to size/time limits).
- **Job routes** return `job_id`; poll status/download endpoints until complete.
- **Event/stream routes** (domain modules) emit progress for long exports.

## Authentication

No built-in authentication middleware is enabled. Terminate TLS and authenticate at the reverse proxy or API gateway.

## Examples

```bash
curl -X POST http://localhost:8000{ctx.routes[0].path if ctx.routes else "/health"} \\
  -F "file=@input.bin"
```

Open interactive docs at `/docs` when running uvicorn locally.

{mcp}
"""


def gen_lifecycle(ctx: ModuleContext) -> str:
    s = ctx.spec
    return f"""# {s.title} Processing Lifecycle

## States

```mermaid
stateDiagram-v2
    [*] --> Received
    Received --> Validating
    Validating --> Processing: ok
    Validating --> Failed: invalid
    Processing --> Writing
    Writing --> Completed
    Processing --> Failed: error
    Failed --> [*]
    Completed --> [*]
```

## Phase detail

| Phase | Description |
|-------|-------------|
| Init | Parse CLI/API options; load settings/env |
| Validate | Verify paths, formats, Content-Type, upload size |
| Process | Run core conversion (`{", ".join(s.entry_functions[:3])}`) |
| Emit | Write Markdown tables/sections/assets |
| Package | Single file, artifact directory, or ZIP |
| Cleanup | Job TTL sweeper removes temp workspaces (API modules) |

## Job lifecycle (HTTP)

{"Job records progress from `queued` → `running` → `completed`/`failed`. Download endpoints stream ZIP bytes when ready." if ctx.spec.has_jobs or any("job" in r.path for r in ctx.routes) else "This module primarily uses synchronous CLI/API responses without a job store."}
"""


def gen_sequence_diagrams(ctx: ModuleContext) -> str:
    s = ctx.spec
    first_route = ctx.routes[0].path if ctx.routes else "/convert/sync"
    return f"""# {s.title} Sequence Diagrams

## Synchronous HTTP conversion

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI
    participant Core as {s.key}_core
    Client->>API: POST {first_route}
    API->>Core: convert
    Core-->>API: artifact bytes/path
    API-->>Client: 200 + body or FileResponse
```

## CLI invocation

```mermaid
sequenceDiagram
    participant User
    participant CLI as {s.cli}
    participant Core as {s.key}_core
    User->>CLI: argv
    CLI->>Core: main()
    Core-->>CLI: exit code
    CLI-->>User: stdout/stderr
```
"""


def gen_remaining_pages(ctx: ModuleContext) -> dict[str, str]:
    s = ctx.spec
    root_rel = f"src/md_generator/{s.src_rel}"
    test_cmd = f"python -m pytest {s.test_dir} -q" if s.test_dir else "python -m pytest -q"
    integrations = "\n".join(f"- {x}" for x in s.integration_items) or "- Standard library and declared PyPI extras."
    pages = {}

    pages["responsibilities.md"] = f"""# {s.title} Responsibilities

## In scope

{integrations}

- Expose `{s.cli}` CLI for local and CI usage.
- Convert {s.input_desc} to {s.output_desc}.
- {"Provide FastAPI + optional MCP integration." if ctx.routes else "Operate as library/CLI tooling without HTTP surface."}

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- {"Application ORM persistence." if not s.has_db else "Mutating source databases (read-only metadata export)."}
"""

    pages["installation.md"] = f"""# {s.title} Installation

## PyPI extra

```bash
pip install "mdengine[{s.extra.split()[0]}]"
```

## Editable development

```bash
pip install -e ".[{s.extra.split(',')[0].strip()},dev]"
```

## HTTP API support

```bash
pip install -e ".[{s.extra.split()[0]},api]"
```

## System dependencies

| Dependency | When needed |
|------------|-------------|
| Python 3.10+ | Always |
| Graphviz `dot` | db/graph ERD or diagram rendering |
| Tesseract / OCR backends | image, ppt, archive nested OCR |
| ffmpeg / imageio-ffmpeg | audio/video |
| Playwright browsers | playwright (`playwright install chromium`) |

See [module README]({repo_link(s.readme_link)}) for module-specific notes.
"""

    pages["configuration.md"] = f"""# {s.title} Configuration

Configuration surfaces:

1. **CLI flags** — `{s.cli} --help`
2. **Environment variables** — see `parameters.md`
3. **Python options classes** — under `{root_rel}`
4. **YAML presets** — {", ".join(f"`{p.relative_to(ROOT)}`" for p in ctx.yaml_configs) or "none packaged"}

## Example

```bash
{s.cli} --help
```

For HTTP services, configure upload limits and CORS via module `settings.py` environment variables.
"""

    pages["database.md"] = (
        f"""# {s.title} Database Notes

This module **exports metadata** from external databases or graphs. It does not define application-owned ORM tables.

## Adapters

{s.extension_notes}

## Consumer databases

See `integration.md` for supported engines and connection URI formats.
"""
        if s.has_db
        else f"""# {s.title} Database Notes

This module does **not** use an application database. All state is ephemeral (temp directories, in-memory job tables) except where job SQLite stores are used by API services.
"""
    )

    pages["exceptions.md"] = f"""# {s.title} Exceptions

## CLI exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Conversion failure |
| 2 | Usage / missing input |

## HTTP errors

| Status | Typical cause |
|--------|----------------|
| 400 | Invalid input/empty upload |
| 413 | Payload exceeds configured MB limit |
| 404 | Unknown job id |
| 500 | Unhandled conversion error |

Wrap calls with retry only for transient network fetch modules (url, youtube); converter failures usually require input fixes.
"""

    pages["logging.md"] = f"""# {s.title} Logging

- Use `-v` / `--verbose` on CLIs where available for stderr diagnostics.
- API modules log job lifecycle at INFO; enable uvicorn access logs in deployment.
- **Do not log secrets** (DB URIs, API keys). Pass via environment variables.
- For support, capture: module name, `{s.cli}` argv (redacted), job id, and first stderr stack trace.
"""

    pages["testing.md"] = f"""# {s.title} Testing

```bash
{test_cmd}
```

Tests live under `{s.test_dir or "**/tests under matching *-to-md folder"}`.

CI currently runs a subset (see root `.github/workflows/ci.yml`); run full module tests locally before merging converter changes.
"""

    pages["deployment.md"] = f"""# {s.title} Deployment

## CLI-only

Install extras in container image; invoke `{s.cli}` as Job/Cron.

## Docker API

If `{s.service}/Dockerfile.api` exists, build and run uvicorn with `--root-path /{s.service}` behind gateway (`deploy/docker-compose.yml`).

## Resources

| Tier | Guidance |
|------|----------|
| CPU | Scale with OCR/Whisper/browser workloads |
| Memory | Large PDFs/archives need higher limits |
| Disk | Temp job workspaces — mount ephemeral volume |

Configure proxy body size and timeouts (see `deploy/nginx/default.conf`).
"""

    pages["lld.md"] = f"""# {s.title} Low-Level Design

## Class and module responsibilities

| Symbol | Responsibility |
|--------|----------------|
{chr(10).join(f"| `{fn}` | Public entry / orchestration |" for fn in s.entry_functions)}

## Call sequence (CLI)

```mermaid
sequenceDiagram
    participant Main as main
    participant Parser as argparse
    participant Core as converter
    Main->>Parser: parse argv
    Parser->>Core: options + paths
    Core-->>Main: result
```

## File map

| Path | Role |
|------|------|
{chr(10).join(f"| `{p.relative_to(ROOT)}` | Implementation |" for p in ctx.py_files[:12])}
| ... | ({len(ctx.py_files)} Python files total) |

{s.extension_notes}
"""

    pages["extension-points.md"] = f"""# {s.title} Extension Points

{s.extension_notes or "Extend via fork of converter pipeline or adding optional backends alongside existing factories."}

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
"""

    pages["performance.md"] = f"""# {s.title} Performance

## Characteristics

| Area | Notes |
|------|-------|
| CPU | Hotspots in parsing, OCR, Whisper, browser capture, graph/DB introspection |
| Memory | Full-file reads for some converters; prefer job API for large inputs |
| Disk | Artifact layouts multiply image/asset size |
| Parallelism | Domain modules may use worker pools (`--workers` on db/log) |

## Recommendations

- Use async job endpoints for large ZIP outputs.
- Pin worker counts to available CPU.
- For batch fleets, horizontal-scale stateless API pods with shared object storage for job artifacts if extended beyond local disk.
"""

    pages["security.md"] = f"""# {s.title} Security

- **Validate uploads**: enforce extension and magic-byte checks where implemented.
- **Path traversal**: write only beneath declared output/job workspace roots.
- **SSRF** (url/playwright): restrict egress in production; allowlist domains.
- **Zip bombs** (archive): rely on size limits and nested depth controls.
- **Resource exhaustion**: configure `MAX_UPLOAD_MB`, job TTL, proxy timeouts.
- **Secrets**: pass DB URIs via env, not CLI in process listings.

No built-in authn/authz — place behind authenticated gateway.
"""

    pages["troubleshooting.md"] = f"""# {s.title} Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `command not found` | Extra not installed / venv inactive | `pip install -e ".[{s.extra.split()[0]}]"` |
| Import error for backend | Missing optional dependency | Install correct extra (`image-ocr`, etc.) |
| HTTP 413 | Upload too large | Raise env limit or use job endpoint |
| Empty Markdown | Wrong options or unsupported input variant | Re-run with `-v`, verify input sample |
| Job stuck | Worker crash / disk full | Check API logs; clean temp dir |

## Debug commands

```bash
{s.cli} --help
python -c "import {s.package}; print('ok')"
```
"""

    pages["examples.md"] = f"""# {s.title} Examples

## CLI

```bash
pip install "mdengine[{s.extra.split()[0]}]"
{s.cli} --help
```

## Python

```python
import {s.package.split(".")[0]}.{s.package.split(".")[1]}{"." + s.package.split(".")[2] if len(s.package.split(".")) > 2 else ""}  # adjust import
# See entry functions: {", ".join(s.entry_functions[:2])}
```

## HTTP

```bash
uvicorn {s.package}.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```
"""

    pages["cli-reference.md"] = f"""# {s.title} CLI Reference

Command: **`{s.cli}`**  
{("Alternate: `" + s.cli_alt + "`") if s.cli_alt else ""}

## Arguments

{table(["Name", "Type", "Required", "Default", "Choices", "Description"], cli_arg_rows(ctx.cli_args))}

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
"""

    pages["integration.md"] = f"""# {s.title} Integrations

{integrations}

## Related documentation

{chr(10).join(f"- [{Path(d).name}]({repo_link(d)})" for d in s.deep_docs) if s.deep_docs else f"- [Module README]({repo_link(s.readme_link)})"}

## MCP

{"Install `mdengine[mcp]` for tool server exposure on supported APIs." if s.has_mcp and ctx.routes else "Not applicable or CLI-only."}
"""

    pages["compatibility.md"] = f"""# {s.title} Compatibility

| Item | Support |
|------|---------|
| Python | 3.10+ (per `pyproject.toml`) |
| OS | Windows, Linux, macOS (module-specific native deps may vary) |
| PyPI extra | `{s.extra}` |
| Input | {s.input_desc} |

Test your target input versions in CI with fixtures under `{s.test_dir or "*-to-md/tests"}`.
"""

    pages["best-practices.md"] = f"""# {s.title} Best Practices

- Install only required extras in production images.
- Pin versions in internal mirrors for reproducible builds.
- Use artifact layout when downstream tools expect `document.md` + `assets/`.
- For APIs, terminate TLS at gateway, enforce auth, and scan uploads if sources are untrusted.
- Store outputs in object storage for large batch pipelines; keep local disk for dev only.
"""

    pages["developer-guide.md"] = f"""# {s.title} Developer Guide

## Layout

- Source: `{root_rel}`
- Tests: `{s.test_dir or "matching *-to-md/tests"}`
- Docs: `docs/modules/{s.key}/`

## Local loop

```bash
pip install -e ".[dev,{s.extra.split()[0]},api]"
{test_cmd}
{s.cli} --help
```

## Where to change behavior

- CLI parsing: `{", ".join(str(p.relative_to(ROOT)) for p in ctx.cli_paths) or "cli module"}`
- Core logic: search `{root_rel}` for `convert` / `extract` functions
- API routes: `{ctx.api_path.relative_to(ROOT) if ctx.api_path else "N/A"}`

## Contributing

- Add tests alongside existing `*-to-md/tests` patterns.
- Update this documentation by re-running `python scripts/generate_module_docs.py --module {s.key}`.
"""

    return pages


def generate_module(spec: ModuleSpec, *, force: bool = False) -> None:
    ctx = build_context(spec)
    out_dir = DOCS / spec.key
    generators = {
        "overview.md": gen_overview,
        "parameters.md": gen_parameters,
        "usecases.md": gen_usecases,
        "workflows.md": gen_workflows,
        "architecture.md": gen_architecture,
        "api.md": gen_api,
        "lifecycle.md": gen_lifecycle,
        "sequence-diagrams.md": gen_sequence_diagrams,
    }
    for name, fn in generators.items():
        merge_write(out_dir / name, fn(ctx), force=force)
    for name, content in gen_remaining_pages(ctx).items():
        merge_write(out_dir / name, content, force=force)


def generate_reference_api(spec: ModuleSpec, ctx: ModuleContext) -> None:
    s = spec
    cli_rows = cli_arg_rows(ctx.cli_args)[:15]
    fn_rows = [[fn, "callable", "—"] for fn in s.entry_functions]
    path = REF_API / f"{s.key}.md"
    content = f"""# `{s.package}` API Reference

## Summary

| Item | Value |
|------|-------|
| Purpose | Convert {s.input_desc} to {s.output_desc} |
| CLI | `{s.cli}` |
| Extra | `{s.extra}` |
| Tier | `{s.tier}` |

## Quick CLI reference

{table(["Argument", "Type", "Required", "Default", "Choices", "Help"], cli_rows)}

## Primary symbols

{table(["Symbol", "Kind", "Notes"], fn_rows)}

## Python API (mkdocstrings)

::: {s.package}
    options:
      show_source: false
      show_root_heading: true
      show_signature_annotations: true
      members_order: source
      filters:
        - "!^_"
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_module_nav_yaml(spec: ModuleSpec) -> str:
    lines = [f"      - {spec.title}:"]
    for group_name, files in NAV_GROUPS:
        lines.append(f"          - {group_name}:")
        for f in files:
            label = f.replace(".md", "").replace("-", " ").title()
            lines.append(f"              - {label}: modules/{spec.key}/{f}")
    return "\n".join(lines)


def update_mkdocs_nav() -> None:
    text = read_text(MKDOCS)
    start = text.index("  - Modules:")
    end = text.index("  - API:", start)
    nav_blocks = ["  - Modules:"]
    for spec in MODULES:
        nav_blocks.append(build_module_nav_yaml(spec))
    new_nav = "\n".join(nav_blocks) + "\n"
    updated = text[:start] + new_nav + text[end:]
    MKDOCS.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate enriched module documentation")
    parser.add_argument("--module", action="append", help="Module key (repeatable). Default: all")
    parser.add_argument("--skip-mkdocs", action="store_true", help="Do not rewrite mkdocs.yml nav")
    parser.add_argument("--skip-reference", action="store_true", help="Skip reference/api pages")
    parser.add_argument("--force", action="store_true", help="Overwrite existing pages")
    args = parser.parse_args()
    keys = {m.key for m in MODULES}
    selected = MODULES
    if args.module:
        unknown = set(args.module) - keys
        if unknown:
            raise SystemExit(f"Unknown modules: {', '.join(sorted(unknown))}")
        selected = [m for m in MODULES if m.key in args.module]
    for spec in selected:
        print(f"Generating docs for {spec.key}...")
        ctx = build_context(spec)
        generate_module(spec, force=args.force)
        if not args.skip_reference:
            generate_reference_api(spec, ctx)
    if not args.skip_mkdocs and not args.module:
        print("Updating mkdocs.yml navigation...")
        update_mkdocs_nav()
    elif not args.skip_mkdocs and args.module:
        print("Skipping mkdocs.yml update for partial run (use full run to refresh nav).")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
