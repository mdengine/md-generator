# Image OCR Extension Points

OCR backends under `image/backends/` (tesseract, paddle, easy).

## Safe extension patterns

- Add adapter implementations and register in factory modules.
- Add optional extras in `pyproject.toml` for heavy dependencies.
- Keep CLI/API thin — delegate to core functions for testability.
