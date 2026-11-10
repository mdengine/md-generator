<#
.SYNOPSIS
  Re-run all md-* generator modules on example inputs with output directed to example/v1/.

.DESCRIPTION
  Executes command-prompt CLI tools across all supported modules:
  - Documents: md-pdf, md-word, md-ppt, md-xlsx, md-zip, md-text, md-image
  - Databases: md-db (SQLite & MS Access)
  - Logs & Telemetry: md-log & md-otel
  - OpenAPI: md-openapi (Swagger 2.0 & OpenAPI 3.0)
  - Media: md-audio & md-video (Whisper transcription)
  - Codeflow: md-codeflow scan
  - Enterprise: md-sap, md-odata, md-graph
  - Web: md-url
  - Unified: mdengine

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts/run-all-v1.ps1
#>
[CmdletBinding()]
param(
    [string] $RepoRoot = "",
    [string] $OutDir = "",
    [switch] $SkipWhisper
)

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$ExampleDir = Join-Path $RepoRoot "example"
if (-not $OutDir) {
    $OutDir = Join-Path $ExampleDir "v1"
}

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  MD-GENERATOR: Run All Modules -> example/v1" -ForegroundColor Cyan
Write-Host "  Repo Root: $RepoRoot" -ForegroundColor Gray
Write-Host "  Output Dir: $OutDir" -ForegroundColor Gray
Write-Host "==============================================================" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$results = @()

function Run-Step([string]$Category, [string]$Module, [string]$Desc, [scriptblock]$Action) {
    Write-Host ""
    Write-Host "[$Category] $Module - $Desc" -ForegroundColor Yellow
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = "PASS"
    $err = ""
    try {
        & $Action
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
            throw "Process exited with code $LASTEXITCODE"
        }
    }
    catch {
        $status = "FAIL"
        $err = $_.ToString()
        Write-Host "  FAILED: $err" -ForegroundColor Red
    }
    $sw.Stop()
    $sec = [math]::Round($sw.Elapsed.TotalSeconds, 2)
    if ($status -eq "PASS") {
        Write-Host "  PASSED ($($sec)s)" -ForegroundColor Green
    }
    $script:results += [PSCustomObject]@{
        Category = $Category
        Module   = $Module
        Target   = $Desc
        Status   = $status
        Duration = "$($sec)s"
        Error    = $err
    }
}

# Ensure sample.graphml exists for graph-to-md test
$graphSamplePath = Join-Path $OutDir "sample.graphml"
if (-not (Test-Path $graphSamplePath)) {
    python -c "import networkx as nx; g = nx.DiGraph(); g.add_node('user1', label='User', name='Alice'); g.add_node('prod1', label='Product', title='Widget'); g.add_edge('user1', 'prod1', type='PURCHASED', weight=1.0); nx.write_graphml(g, r'$graphSamplePath')"
}

# --- Category 1: Documents & Archives ---
$cliOut = Join-Path $OutDir "cli-output"
New-Item -ItemType Directory -Force -Path $cliOut | Out-Null

Run-Step "Document" "md-pdf" "PDF Sub_Order_Labels" {
    $dest = Join-Path $cliOut "pdf_Sub_Order_Labels"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-pdf (Join-Path $ExampleDir "pdf\Sub_Order_Labels_2b0d27f5-64d1-4d04-aafc-921ce54ed043.pdf") $dest --artifact-layout
}

Run-Step "Document" "md-word" "Word ATS Resume" {
    $dest = Join-Path $cliOut "word_Resume"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-word (Join-Path $ExampleDir "word\Vishal_Shah_ATS_Resume.docx") (Join-Path $dest "document.md") --images-dir (Join-Path $dest "images")
}

Run-Step "Document" "md-ppt" "PPTX Salamat matrutv" {
    $dest = Join-Path $cliOut "ppt_Salamat"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-ppt (Join-Path $ExampleDir "ppt\Salamat matrutv.pptx") $dest --artifact-layout --no-extract-embedded-deep
}

Run-Step "Document" "md-xlsx" "XLSX CHINGS ITEM" {
    $dest = Join-Path $cliOut "xlsx_CHINGS"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-xlsx -i (Join-Path $ExampleDir "xlsx\CHINGS ITEM.xlsx") -o $dest
}

Run-Step "Document" "md-xlsx" "CSV Radhika Marketing" {
    $dest = Join-Path $cliOut "csv_Radhika"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-xlsx -i (Join-Path $ExampleDir "xlsx\Radhika Marketing - Exported Products.csv") -o $dest
}

Run-Step "Document" "md-zip" "ZIP Sample_Example" {
    $dest = Join-Path $cliOut "zip_Sample"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-zip (Join-Path $ExampleDir "zip\Sample_Example.zip") $dest
}

Run-Step "Document" "md-text" "JSON sample_json" {
    $dest = Join-Path $cliOut "json_sample"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-text (Join-Path $ExampleDir "xml-json\sample_json.json") (Join-Path $dest "document.md")
}

Run-Step "Document" "md-text" "XML sample_xml" {
    $dest = Join-Path $cliOut "xml_sample"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-text (Join-Path $ExampleDir "xml-json\sample_xml.xml") (Join-Path $dest "document.md")
}

Run-Step "Document" "md-image" "Image Screenshot" {
    $dest = Join-Path $cliOut "image_screenshot"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    & md-image (Join-Path $ExampleDir "image\Screenshot 2023-09-03 230520.png") (Join-Path $dest "document.md") --engines tess --strategy best --title Screenshot
}

# --- Category 2: Databases ---
$dbOut = Join-Path $OutDir "db"
New-Item -ItemType Directory -Force -Path $dbOut | Out-Null

Run-Step "Database" "md-db" "SQLite sakila" {
    $dest = Join-Path $dbOut "sakila"
    & md-db --type sqlite --uri "sqlite:///example/db/sakila.db" --output $dest
}

Run-Step "Database" "md-db" "SQLite chinook" {
    $dest = Join-Path $dbOut "chinook"
    & md-db --type sqlite --uri "sqlite:///example/db/Chinook_Sqlite.sqlite" --output $dest
}

Run-Step "Database" "md-db" "SQLite northwind" {
    $dest = Join-Path $dbOut "northwind"
    & md-db --type sqlite --uri "sqlite:///example/db/northwind_small.sqlite" --output $dest
}

Run-Step "Database" "md-db" "MS Access accdb" {
    $dest = Join-Path $dbOut "access_vba"
    $uri = "access:///?odbc_connect=DRIVER%3D%7BMicrosoft+Access+Driver+%28%2A.mdb%2C+%2A.accdb%29%7D%3BDBQ%3DC%3A%5CTask%5CProject%5Cmd-generator%5Cexample%5Cdb%5CAccess_Example_VBA.accdb%3B"
    & md-db --type access --uri $uri --output $dest
}

Run-Step "Database" "md-db" "MS Access mdb" {
    $dest = Join-Path $dbOut "mailing_letter"
    $uri = "access:///?odbc_connect=DRIVER%3D%7BMicrosoft+Access+Driver+%28%2A.mdb%2C+%2A.accdb%29%7D%3BDBQ%3DC%3A%5CTask%5CProject%5Cmd-generator%5Cexample%5Cdb%5Cmailing+letter+V2.mdb%3B"
    & md-db --type access --uri $uri --output $dest
}

# --- Category 3: Logs & Telemetry ---
$logOut = Join-Path $OutDir "log"
$otelOut = Join-Path $OutDir "otel"
New-Item -ItemType Directory -Force -Path $logOut, $otelOut | Out-Null

Run-Step "Telemetry" "md-log" "Python log" {
    $dest = Join-Path $logOut "python"
    & md-log --input (Join-Path $ExampleDir "log\python\app.log") --output $dest --preset generic --frontmatter
}

Run-Step "Telemetry" "md-log" "PHP log" {
    $dest = Join-Path $logOut "php"
    & md-log --input (Join-Path $ExampleDir "log\php\app.log") --output $dest --preset generic --frontmatter
}

Run-Step "Telemetry" "md-log" "Spring Boot log" {
    $dest = Join-Path $logOut "spring"
    & md-log --input (Join-Path $ExampleDir "log\spring\app.log") --output $dest --preset springboot --frontmatter
}

Run-Step "Telemetry" "md-otel" "OTEL Traces" {
    $dest = Join-Path $otelOut "traces"
    & md-otel --input (Join-Path $ExampleDir "otel\otlp-traces.json") --output $dest
}

Run-Step "Telemetry" "md-otel" "OTEL Logs" {
    $dest = Join-Path $otelOut "logs"
    & md-otel --input (Join-Path $ExampleDir "otel\otlp-logs.json") --output $dest
}

# --- Category 4: OpenAPI ---
$openApiOut = Join-Path $OutDir "openapi"
New-Item -ItemType Directory -Force -Path $openApiOut | Out-Null

Run-Step "OpenAPI" "md-openapi" "OpenAPI 2.X YAML" {
    $dest = Join-Path $openApiOut "2X_complex_yaml"
    & md-openapi generate --file (Join-Path $ExampleDir "openapi\2.X\complex.all.yaml") --output $dest
}

Run-Step "OpenAPI" "md-openapi" "OpenAPI 2.X JSON" {
    $dest = Join-Path $openApiOut "2X_complex_json"
    & md-openapi generate --file (Join-Path $ExampleDir "openapi\2.X\comlex.all.json") --output $dest
}

Run-Step "OpenAPI" "md-openapi" "OpenAPI 3.X YAML" {
    $dest = Join-Path $openApiOut "3X_tictactoe"
    & md-openapi generate --file (Join-Path $ExampleDir "openapi\3.X\tictactoe.yaml") --output $dest
}

Run-Step "OpenAPI" "md-openapi" "OpenAPI 3.X JSON" {
    $dest = Join-Path $openApiOut "3X_flight"
    & md-openapi generate --file (Join-Path $ExampleDir "openapi\3.X\flight.openapi.json") --output $dest
}

# --- Category 5: Media (Audio / Video) ---
$mediaOut = Join-Path $OutDir "media"
New-Item -ItemType Directory -Force -Path $mediaOut | Out-Null

if (-not $SkipWhisper) {
    Run-Step "Media" "md-audio" "Audio sample.wav" {
        $dest = Join-Path $mediaOut "sample_wav.md"
        & md-audio (Join-Path $ExampleDir "media\sample.wav") $dest --model tiny
    }

    Run-Step "Media" "md-video" "Video sample.mp4" {
        $dest = Join-Path $mediaOut "sample_video.md"
        & md-video (Join-Path $ExampleDir "media\sample.mp4") $dest --model tiny
    }
}

# --- Category 6: Codeflow ---
$codeflowOut = Join-Path $OutDir "codeflow"
New-Item -ItemType Directory -Force -Path $codeflowOut | Out-Null

Run-Step "Codeflow" "md-codeflow" "Scan odata-to-md" {
    $dest = Join-Path $codeflowOut "odata_scan"
    & md-codeflow scan (Join-Path $RepoRoot "odata-to-md") --output $dest --formats md,mermaid,json,html --depth 3 --lang mixed
}

# --- Category 7: Enterprise (SAP / OData / Graph) ---
$sapOut = Join-Path $OutDir "sap"
$odataOut = Join-Path $OutDir "odata"
$graphOut = Join-Path $OutDir "graph"
New-Item -ItemType Directory -Force -Path $sapOut, $odataOut, $graphOut | Out-Null

Run-Step "Enterprise" "md-sap" "SAP ABAP customer sync" {
    $abapFixture = Join-Path $RepoRoot "sap-to-md\tests\fixtures\abap\z_customer_sync.abap"
    & md-sap $abapFixture --output $sapOut
}

Run-Step "Enterprise" "md-odata" "OData v2 CSDL metadata" {
    $odataFixture = Join-Path $RepoRoot "odata-to-md\tests\fixtures\odata\v2_with_container.xml"
    & md-odata generate --file $odataFixture --output $odataOut --graph --chunk
}

Run-Step "Enterprise" "md-graph" "NetworkX GraphML export" {
    & md-graph --source networkx --graph-file $graphSamplePath --output $graphOut
}

# --- Category 8: Web URL ---
$urlOut = Join-Path $OutDir "url"
New-Item -ItemType Directory -Force -Path $urlOut | Out-Null

Run-Step "Web" "md-url" "HTML URL conversion" {
    & md-url "https://example.com" $urlOut --artifact-layout
}

# --- Category 9: Unified mdengine CLI ---
Run-Step "Unified" "mdengine" "Unified CLI help" {
    & mdengine --help
}

# --- Summary Report ---
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "                    EXECUTION SUMMARY                         " -ForegroundColor Cyan
Write-Host "==============================================================" -ForegroundColor Cyan
$script:results | Format-Table -AutoSize Category, Module, Target, Status, Duration

$failedCount = ($script:results | Where-Object { $_.Status -eq "FAIL" }).Count
$passedCount = ($script:results | Where-Object { $_.Status -eq "PASS" }).Count
$totalCount  = $script:results.Count

Write-Host ""
if ($failedCount -eq 0) {
    Write-Host "RESULT: ALL $totalCount MODULE RUNS PASSED SUCCESSFULLY! (0 failures, no breaks)" -ForegroundColor Green
    exit 0
} else {
    Write-Host "RESULT: $failedCount of $totalCount MODULE RUNS FAILED!" -ForegroundColor Red
    exit 1
}
