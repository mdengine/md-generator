# Log Analysis Security

- **Validate uploads**: enforce extension and magic-byte checks where implemented.
- **Path traversal**: write only beneath declared output/job workspace roots.
- **SSRF** (url/playwright): restrict egress in production; allowlist domains.
- **Zip bombs** (archive): rely on size limits and nested depth controls.
- **Resource exhaustion**: configure `MAX_UPLOAD_MB`, job TTL, proxy timeouts.
- **Secrets**: pass DB URIs via env, not CLI in process listings.

No built-in authn/authz — place behind authenticated gateway.
