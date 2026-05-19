# YouTube Examples

## CLI

```bash
pip install "mdengine[youtube]"
md-youtube --help
```

## Python

```python
import md_generator.media.youtube  # adjust import
# See entry functions: YouTubeToMarkdownService, YouTubeConverter
```

## HTTP

```bash
uvicorn md_generator.media.youtube.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```
