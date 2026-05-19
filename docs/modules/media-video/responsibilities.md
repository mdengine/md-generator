# Video Responsibilities

## In scope

- ffmpeg via imageio-ffmpeg
- Whisper

- Expose `md-video` CLI for local and CI usage.
- Convert Video files to Transcript Markdown with video metadata.
- Provide FastAPI + optional MCP integration.

## Out of scope

- Owning user authentication/authorization for enterprise SSO (delegate to gateway).
- Long-term storage of customer documents (outputs are written to caller-specified paths).
- Application ORM persistence.
