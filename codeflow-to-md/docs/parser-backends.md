# Codeflow parser backends

## Modes (`--parser-mode`)

| Mode | Behavior |
|------|----------|
| `auto` (default) | Native parsers: Java (`javalang`), Python (`ast`), Go (`codeflow_go_dump` + `go` on PATH), PHP (`codeflow_php_dump` + `php`), JS/TS (Tree-sitter when `codeflow-treesitter` installed), C++ (libclang with Tree-sitter fallback). |
| `treesitter` | Tree-sitter for **java**, **python**, **go**, **php**, **cpp**; JS/TS via registry when grammars installed. |
| `external` | C++ **clang only**; other languages fall back to `auto`. |

Install optional grammars:

```bash
pip install "mdengine[codeflow,codeflow-treesitter]"
```

## Java / Spring

```bash
codeflow scan path/to/spring-app --lang java --parser-mode treesitter --include api --emit-cfg
```

Default (unchanged):

```bash
codeflow scan path/to/spring-app --lang java --parser-mode auto
```

## Metadata

Each parsed file records **`parse_backend`** (`native` | `treesitter`) and optional **`grammar_package`** on `FileParseResult`. Scan **`scan-summary.md`** includes a **Parse backends** section.

## Capabilities (read-only)

See `capability_registry.py` — used for warnings only, not routing. Example: Go/PHP `auto` may need external dump tools; `treesitter` mode avoids them when grammars are installed.

## Out of scope (separate epics)

- Central symbol resolver refactor
- File-hash incremental reparse
- `--debug-ir` export
