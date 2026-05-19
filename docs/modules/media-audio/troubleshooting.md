# Audio Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `command not found` | Extra not installed / venv inactive | `pip install -e ".[audio]"` |
| Import error for backend | Missing optional dependency | Install correct extra (`image-ocr`, etc.) |
| HTTP 413 | Upload too large | Raise env limit or use job endpoint |
| Empty Markdown | Wrong options or unsupported input variant | Re-run with `-v`, verify input sample |
| Job stuck | Worker crash / disk full | Check API logs; clean temp dir |

## Debug commands

```bash
md-audio --help
python -c "import md_generator.media.audio; print('ok')"
```
