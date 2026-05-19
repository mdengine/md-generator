# Skill Builder Responsibilities

## In scope

- pyproject.toml scripts
- git diff for --since

- Expose `mdengine skill build` CLI for local and CI usage.
- Convert Project metadata to Structured skills under ai/.
- Operate as library/CLI tooling without HTTP surface.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.
