# AI Assistant Tools CLI Reference

Command: **`mdengine ai assist`**  
Alternate: `mdengine ai export`

## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `query` | str | required | — | — | Natural language query |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |
| `--format` | str | optional | — | ('openai', 'claude', 'cursor') | — |
| `--query` | str | optional | — | — | Natural language query |
| `--output` | str | optional | None | — | Write to file instead of stdout. |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |
| `query` | str | required | — | — | Natural language query |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |
| `--format` | str | optional | — | ('openai', 'claude', 'cursor') | — |
| `--query` | str | optional | — | — | Natural language query |
| `--output` | str | optional | None | — | Write to file instead of stdout. |
| `--rag` | flag | optional | false | — | Use Chroma RAG when installed. |
| `--ai-root` | str | optional | None | — | Override MDENGINE_SKILL_AI_ROOT for this run. |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
