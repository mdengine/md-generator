# Parser design

## ABAP

Hybrid lexer (comment/string aware) + statement regex extractors. Outputs `AbapAnalysis` JSON.

## CDS

Regex-based `define view` parser with annotation and association extraction. Semantic entity from `@Semantics.businessObject` or name heuristics.

## DDIC

CSV DD02L/DD03L exports → `DdicTable` with inferred business names.

## OData / BAPI / IDoc / Transport

XML/JSON parsers for `$metadata.xml`, BAPI exports, IDoc definitions, transport CSV.

## Extension

Register custom parsers in YAML:

```yaml
parser:
  plugins:
    - mycorp.sap_plugin:MyParser
```
