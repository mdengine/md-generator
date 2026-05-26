# Codeflow parser backends

## Modes (`--parser-mode`)

| Mode | Behavior |
|------|----------|
| `auto` (default) | Native parsers: Java (`javalang`), Python (`ast`), Go (`codeflow_go_dump` + `go` on PATH), PHP (`codeflow_php_dump` + `php`), JS/TS (Tree-sitter when `codeflow-treesitter` installed), C++ (libclang with Tree-sitter fallback), **Rust / Kotlin / C# / Swift / Ruby / Lua** (Tree-sitter when extra installed). |
| `treesitter` | Tree-sitter for **java**, **python**, **go**, **php**, **cpp**, **rust**, **kotlin**, **csharp**, **swift**, **ruby**, **lua**; JS/TS via registry when grammars installed. |
| `external` | C++ **clang only**; other languages fall back to `auto`. |

## Parser resolution matrix

| Language | `auto` | `treesitter` | `external` |
|----------|--------|--------------|------------|
| Java | javalang (native) | tree-sitter-java | falls back to `auto` |
| Python | ast (native) | tree-sitter-python | falls back to `auto` |
| Go | codeflow_go_dump (native) | tree-sitter-go | falls back to `auto` |
| PHP | codeflow_php_dump (native) | tree-sitter-php | falls back to `auto` |
| JS / TS / TSX | tree-sitter-* (registry) | same | falls back to `auto` |
| C++ | libclang (+ TS fallback) | tree-sitter-cpp | **clang only** |
| Rust | tree-sitter-rust (registry) | same | falls back to `auto` |
| Kotlin | tree-sitter-kotlin (registry) | same | falls back to `auto` |
| C# | tree-sitter-c-sharp (registry) | same | falls back to `auto` |
| Swift | tree-sitter-swift (registry) | same | falls back to `auto` |
| Ruby | tree-sitter-ruby (registry) | same | falls back to `auto` |
| Lua | tree-sitter-lua (registry) | same | falls back to `auto` |

Install optional grammars:

```bash
pip install "mdengine[codeflow,codeflow-treesitter]"
```

Note: `tree-sitter-swift` uses the 0.7.x release line (pinned separately from 0.23.x grammars).

## Java / Spring

```bash
codeflow scan path/to/spring-app --lang java --parser-mode treesitter --include api --emit-cfg
```

Default (unchanged):

```bash
codeflow scan path/to/spring-app --lang java --parser-mode auto
```

## Rust / Kotlin / C#

```bash
codeflow scan path/to/rust-crate --lang rust --emit-cfg
codeflow scan path/to/kotlin-app --lang kotlin --include api
codeflow scan path/to/aspnet-app --lang csharp --include api
```

## Swift / Ruby / Lua

```bash
codeflow scan path/to/ios-app --lang swift --emit-cfg
codeflow scan path/to/rails-app --lang ruby --emit-cfg
codeflow scan path/to/lua-app --lang lua --emit-cfg
```

Tree-sitter is the only backend for Rust, Kotlin, C#, Swift, Ruby, and Lua today (`parse_backend=treesitter` in scan output).

## Metadata

Each parsed file records **`parse_backend`** (`native` | `treesitter`), optional **`grammar_package`**, and **`parse_had_errors`** when Tree-sitter reports syntax errors (partial graph may still be emitted). Scan **`scan-summary.md`** includes a **Parse backends** section.

## Symbol IDs

All Tree-sitter parsers use `{repo_relative_path}::{Class}.{method}` via `treesitter_common.sid()` (e.g. `src/App.kt::App.run`, `Demo.swift::ClassA.a`, `demo.rb::ClassA::a`).

## Grammar upgrades

Bump `codeflow-treesitter` pins only after fixture tests pass and note changes here.

## Capabilities (read-only)

See `capability_registry.py` — used for warnings only, not routing. Fields include `imports`, `calls`, `entries` (`True` | `False` | `"partial"`).

## Out of scope (separate epics)

- Central symbol resolver refactor
- File-hash incremental reparse
- `--debug-ir` export
- Native Rust/Kotlin/C#/Swift/Ruby/Lua compiler backends
- Unknown-extension Tree-sitter fallback
