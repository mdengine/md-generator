# Examples — codeflow

## Basic scan

```bash
pip install "mdengine[codeflow]"
md-codeflow scan ./my-repo --output ./codeflow-out
# or: codeflow scan ./my-repo --output ./codeflow-out
```

## Tree-sitter parsers (multi-language)

```bash
pip install "mdengine[codeflow,codeflow-treesitter]"
md-codeflow scan ./polyglot-repo --output ./out
```

Supported via **`codeflow-treesitter`** (install pulls language grammars): JavaScript/TypeScript, Python, Java, Go, C/C++, Rust, Kotlin, C#, Swift, Ruby, Lua, Scala, Zig, PHP, and related Tree-sitter bindings listed in `pyproject.toml`.

## C/C++ with libclang

```bash
pip install "mdengine[codeflow,codeflow-clang]"
md-codeflow scan ./native-project --output ./out
```

## Semantic clustering (large install)

```bash
pip install "mdengine[codeflow,codeflow-semantic]"
```

## API + MCP

```bash
pip install "mdengine[codeflow,api,mcp]"
md-codeflow-api
md-codeflow-mcp --transport stdio
```

## Meta-router

```bash
mdengine codeflow-to-md scan ./my-repo --output ./out
```
