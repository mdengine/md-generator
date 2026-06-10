# Navigation index (`navigation/index.json`)

Version **1.0.0** — stable contract for tooling, graph bootstrap, and UI navigation.

## Location

Written by pipeline v2 after canonical markdown generation:

`navigation/index.json`

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string (semver) | Contract version; bump major on breaking changes |
| `generated_at` | ISO 8601 UTC | Generation timestamp |
| `run_id` | string | Pipeline run identifier |
| `entries` | array | One object per registered DDIC/canonical artifact |

### Entry object

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | DDIC object name (uppercase) |
| `kind` | string | Path kind (`DATA_ELEMENT`, `DOMAIN`, `STRUCTURE`, …) |
| `stable_id` | string | Canonical stable identifier |
| `artifact_type` | string | Canonical artifact type (e.g. `ddic.data_element`) |
| `paths.entity` | string | v1 entity markdown path (when present) |
| `paths.canonical` | string | v2 canonical markdown path |

## Example

```json
{
  "schema_version": "1.0.0",
  "generated_at": "2026-05-20T12:00:00Z",
  "run_id": "1716206400",
  "entries": [
    {
      "name": "CHAR100",
      "kind": "DATA_ELEMENT",
      "stable_id": "DDIC::DATA_ELEMENT::CHAR100",
      "artifact_type": "ddic.data_element",
      "paths": {
        "entity": "entities/szs_char100.md",
        "canonical": "ddic/data-elements/char100.md"
      }
    }
  ]
}
```

## Versioning

- **Patch**: documentation-only or optional fields
- **Minor**: new optional entry fields
- **Major**: removed/renamed required fields or semantic changes to `paths`
