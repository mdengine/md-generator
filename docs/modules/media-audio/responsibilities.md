# Audio Responsibilities

## In scope

- openai-whisper
- imageio-ffmpeg

- Expose `md-audio` CLI for local and CI usage.
- Convert Audio files to Whisper transcript Markdown.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.
