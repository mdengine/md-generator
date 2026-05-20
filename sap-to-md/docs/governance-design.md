# Governance design

Field-level classification uses pattern rules on field names, domains, and table prefixes:

- **PII** — email, phone, name patterns
- **FINANCIAL** — amount, bank, tax fields
- **HR_SENSITIVE** — salary, PA* tables

Output: `governance/fields.json` and per-entity governance Markdown sections.
