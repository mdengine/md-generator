# AI Assistant Tools Responsibilities

## In scope

- OpenAI optional
- Chroma RAG optional

- Expose `mdengine ai assist` CLI for local and CI usage.
- Convert Skill bundles and prompts to Assembled context and assistant output.
- Operate as library/CLI tooling without HTTP surface.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.
