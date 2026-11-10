#!/usr/bin/env bash
# ==============================================================================
# Re-run all md-* generator modules on example inputs with output -> example/v1/
# Cross-platform runner for Linux, macOS, and POSIX environments (WSL, Git Bash).
# Usage (from repo root): bash scripts/run-all-v1.sh
# ==============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE_DIR="${EXAMPLE_DIR:-$REPO_ROOT/example}"
OUT_DIR="${OUT_DIR:-$EXAMPLE_DIR/v1}"
CLI_OUT="$OUT_DIR/cli-output"
cd "$REPO_ROOT"

echo "=============================================================="
echo "  MD-GENERATOR: Run All Modules -> example/v1 (Linux/macOS)"
echo "  Repo Root:  $REPO_ROOT"
echo "  Output Dir: $OUT_DIR"
echo "=============================================================="

mkdir -p "$OUT_DIR" "$CLI_OUT"

# Generate graphml sample if missing
GRAPH_SAMPLE="$OUT_DIR/sample.graphml"
if [ ! -f "$GRAPH_SAMPLE" ]; then
  python3 -c "import networkx as nx; g = nx.DiGraph(); g.add_node('user1', label='User', name='Alice'); g.add_node('prod1', label='Product', title='Widget'); g.add_edge('user1', 'prod1', type='PURCHASED', weight=1.0); nx.write_graphml(g, '$GRAPH_SAMPLE')" 2>/dev/null || \
  python -c "import networkx as nx; g = nx.DiGraph(); g.add_node('user1', label='User', name='Alice'); g.add_node('prod1', label='Product', title='Widget'); g.add_edge('user1', 'prod1', type='PURCHASED', weight=1.0); nx.write_graphml(g, '$GRAPH_SAMPLE')" 2>/dev/null || true
fi

passed=0
failed=0

run_step() {
  local category="$1"
  local module="$2"
  local desc="$3"
  shift 3
  echo ""
  echo "[$category] $module - $desc"
  if "$@"; then
    echo "  PASSED"
    passed=$((passed + 1))
  else
    echo "  FAILED (exit $?)"
    failed=$((failed + 1))
  fi
}

# --- 1. Documents ---
mkdir -p "$CLI_OUT/pdf_Sub_Order_Labels" "$CLI_OUT/word_Resume" "$CLI_OUT/ppt_Salamat" \
         "$CLI_OUT/xlsx_CHINGS" "$CLI_OUT/csv_Radhika" "$CLI_OUT/zip_Sample" \
         "$CLI_OUT/json_sample" "$CLI_OUT/xml_sample" "$CLI_OUT/image_screenshot"

run_step "Document" "md-pdf" "PDF Sub_Order_Labels" \
  md-pdf "$EXAMPLE_DIR/pdf/Sub_Order_Labels_2b0d27f5-64d1-4d04-aafc-921ce54ed043.pdf" "$CLI_OUT/pdf_Sub_Order_Labels" --artifact-layout

run_step "Document" "md-word" "Word ATS Resume" \
  md-word "$EXAMPLE_DIR/word/Vishal_Shah_ATS_Resume.docx" "$CLI_OUT/word_Resume/document.md" --images-dir "$CLI_OUT/word_Resume/images"

run_step "Document" "md-ppt" "PPTX Salamat matrutv" \
  md-ppt "$EXAMPLE_DIR/ppt/Salamat matrutv.pptx" "$CLI_OUT/ppt_Salamat" --artifact-layout --no-extract-embedded-deep

run_step "Document" "md-xlsx" "XLSX CHINGS ITEM" \
  md-xlsx -i "$EXAMPLE_DIR/xlsx/CHINGS ITEM.xlsx" -o "$CLI_OUT/xlsx_CHINGS"

run_step "Document" "md-xlsx" "CSV Radhika Marketing" \
  md-xlsx -i "$EXAMPLE_DIR/xlsx/Radhika Marketing - Exported Products.csv" -o "$CLI_OUT/csv_Radhika"

run_step "Document" "md-zip" "ZIP Sample_Example" \
  md-zip "$EXAMPLE_DIR/zip/Sample_Example.zip" "$CLI_OUT/zip_Sample"

run_step "Document" "md-text" "JSON sample_json" \
  md-text "$EXAMPLE_DIR/xml-json/sample_json.json" "$CLI_OUT/json_sample/document.md"

run_step "Document" "md-text" "XML sample_xml" \
  md-text "$EXAMPLE_DIR/xml-json/sample_xml.xml" "$CLI_OUT/xml_sample/document.md"

run_step "Document" "md-image" "Image Screenshot" \
  md-image "$EXAMPLE_DIR/image/Screenshot 2023-09-03 230520.png" "$CLI_OUT/image_screenshot/document.md" --engines tess --strategy best --title Screenshot

# --- 2. Databases ---
mkdir -p "$OUT_DIR/db/sakila" "$OUT_DIR/db/chinook" "$OUT_DIR/db/northwind"
run_step "Database" "md-db" "SQLite sakila" \
  md-db --type sqlite --uri "sqlite:///example/db/sakila.db" --output "$OUT_DIR/db/sakila"

run_step "Database" "md-db" "SQLite chinook" \
  md-db --type sqlite --uri "sqlite:///example/db/Chinook_Sqlite.sqlite" --output "$OUT_DIR/db/chinook"

run_step "Database" "md-db" "SQLite northwind" \
  md-db --type sqlite --uri "sqlite:///example/db/northwind_small.sqlite" --output "$OUT_DIR/db/northwind"

# --- 3. Telemetry ---
mkdir -p "$OUT_DIR/log/python" "$OUT_DIR/log/php" "$OUT_DIR/log/spring" "$OUT_DIR/otel/traces" "$OUT_DIR/otel/logs"
run_step "Telemetry" "md-log" "Python log" \
  md-log --input "$EXAMPLE_DIR/log/python/app.log" --output "$OUT_DIR/log/python" --preset generic --frontmatter

run_step "Telemetry" "md-log" "PHP log" \
  md-log --input "$EXAMPLE_DIR/log/php/app.log" --output "$OUT_DIR/log/php" --preset generic --frontmatter

run_step "Telemetry" "md-log" "Spring Boot log" \
  md-log --input "$EXAMPLE_DIR/log/spring/app.log" --output "$OUT_DIR/log/spring" --preset springboot --frontmatter

run_step "Telemetry" "md-otel" "OTEL Traces" \
  md-otel --input "$EXAMPLE_DIR/otel/otlp-traces.json" --output "$OUT_DIR/otel/traces"

run_step "Telemetry" "md-otel" "OTEL Logs" \
  md-otel --input "$EXAMPLE_DIR/otel/otlp-logs.json" --output "$OUT_DIR/otel/logs"

# --- 4. OpenAPI ---
mkdir -p "$OUT_DIR/openapi/2X_complex_yaml" "$OUT_DIR/openapi/2X_complex_json" \
         "$OUT_DIR/openapi/3X_tictactoe" "$OUT_DIR/openapi/3X_flight"

run_step "OpenAPI" "md-openapi" "OpenAPI 2.X YAML" \
  md-openapi generate --file "$EXAMPLE_DIR/openapi/2.X/complex.all.yaml" --output "$OUT_DIR/openapi/2X_complex_yaml"

run_step "OpenAPI" "md-openapi" "OpenAPI 2.X JSON" \
  md-openapi generate --file "$EXAMPLE_DIR/openapi/2.X/comlex.all.json" --output "$OUT_DIR/openapi/2X_complex_json"

run_step "OpenAPI" "md-openapi" "OpenAPI 3.X YAML" \
  md-openapi generate --file "$EXAMPLE_DIR/openapi/3.X/tictactoe.yaml" --output "$OUT_DIR/openapi/3X_tictactoe"

run_step "OpenAPI" "md-openapi" "OpenAPI 3.X JSON" \
  md-openapi generate --file "$EXAMPLE_DIR/openapi/3.X/flight.openapi.json" --output "$OUT_DIR/openapi/3X_flight"

# --- 5. Media ---
if [ "${SKIP_WHISPER:-0}" != "1" ]; then
  mkdir -p "$OUT_DIR/media"
  run_step "Media" "md-audio" "Audio sample.wav" \
    md-audio "$EXAMPLE_DIR/media/sample.wav" "$OUT_DIR/media/sample_wav.md" --model tiny

  run_step "Media" "md-video" "Video sample.mp4" \
    md-video "$EXAMPLE_DIR/media/sample.mp4" "$OUT_DIR/media/sample_video.md" --model tiny
fi

# --- 6. Codeflow ---
mkdir -p "$OUT_DIR/codeflow/odata_scan"
run_step "Codeflow" "md-codeflow" "Scan odata-to-md" \
  md-codeflow scan "$REPO_ROOT/odata-to-md" --output "$OUT_DIR/codeflow/odata_scan" --formats md,mermaid,json,html --depth 3 --lang mixed

# --- 7. Enterprise ---
mkdir -p "$OUT_DIR/sap" "$OUT_DIR/odata" "$OUT_DIR/graph"
run_step "Enterprise" "md-sap" "SAP ABAP customer sync" \
  md-sap "$REPO_ROOT/sap-to-md/tests/fixtures/abap/z_customer_sync.abap" --output "$OUT_DIR/sap"

run_step "Enterprise" "md-odata" "OData v2 CSDL metadata" \
  md-odata generate --file "$REPO_ROOT/odata-to-md/tests/fixtures/odata/v2_with_container.xml" --output "$OUT_DIR/odata" --graph --chunk

run_step "Enterprise" "md-graph" "NetworkX GraphML export" \
  md-graph --source networkx --graph-file "$GRAPH_SAMPLE" --output "$OUT_DIR/graph"

# --- 8. Web ---
mkdir -p "$OUT_DIR/url"
run_step "Web" "md-url" "HTML URL conversion" \
  md-url "https://example.com" "$OUT_DIR/url" --artifact-layout

# --- 9. Unified CLI ---
run_step "Unified" "mdengine" "Unified CLI help" \
  mdengine --help

echo ""
echo "=============================================================="
echo "  SUMMARY: $passed passed, $failed failed"
echo "=============================================================="

if [ "$failed" -eq 0 ]; then
  echo "All module runs passed on POSIX/Linux/macOS!"
  exit 0
else
  echo "Some module runs failed."
  exit 1
fi
