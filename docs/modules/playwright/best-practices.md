# Playwright Web Capture Best Practices

- Install only required extras in production images.
- Pin versions in internal mirrors for reproducible builds.
- Use artifact layout when downstream tools expect `document.md` + `assets/`.
- For APIs, terminate TLS at gateway, enforce auth, and scan uploads if sources are untrusted.
- Store outputs in object storage for large batch pipelines; keep local disk for dev only.
