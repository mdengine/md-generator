# Video Examples

## CLI

```bash
pip install "mdengine[video]"
md-video --help
```

## Python

```python
import md_generator.media.video  # adjust import
# See entry functions: VideoToMarkdownService, video_probe_from_ffprobe
```

## HTTP

```bash
uvicorn md_generator.media.video.api.main:app --reload --port 8000
# Open http://localhost:8000/docs
```
