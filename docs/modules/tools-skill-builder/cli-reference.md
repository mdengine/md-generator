# Skill Builder CLI Reference

Command: **`mdengine skill build`**  


## Arguments

| Name | Type | Required | Default | Choices | Description |
| --- | --- | --- | --- | --- | --- |
| `--since` | str | optional | None | — | Only regenerate area skills touched under src/md_generator since GIT_REF (global/graph/registry still refresh). |
| `--root` | Path | optional | _REPO_ROOT | — | Repository root (default: inferred from this file). |


## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime conversion failure |
| 2 | Invalid usage or missing input |
