from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_journey_scan_integration(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "mini_python"
    out = tmp_path / "out"
    
    env = dict(**__import__("os").environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    
    r = subprocess.run(
        [
            sys.executable,
            "-m", "md_generator.codeflow.cli.main",
            "scan", str(root),
            "--output", str(out),
            "--depth", "3",
            "--journey",
            "--journey-format", "md,json,mermaid,html",
            "--journey-paths",
            "--journey-statistics",
            "--emit-entry-per-method",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    
    assert r.returncode == 0, r.stderr + r.stdout
    
    # 1. Full repository summary
    repo_summary = out / "repository-journey-summary.md"
    assert repo_summary.is_file()
    assert "# Repository Journey Summary" in repo_summary.read_text(encoding="utf-8")
    
    # 2. Check per-method journey outputs
    # Let's see if the methods/ folder is created
    methods_dir = out / "methods"
    assert methods_dir.is_dir()
    
    # Let's find one method subdirectory and check its files
    subdirs = list(methods_dir.iterdir())
    assert len(subdirs) > 0
    
    # The first directory should contain all journey formats
    sub = subdirs[0]
    assert (sub / "journey.md").is_file()
    assert (sub / "journey.json").is_file()
    assert (sub / "journey.mmd").is_file()
    assert (sub / "journey.html").is_file()
    
    # Execution paths and analyzer output
    assert (sub / "execution-paths.md").is_file()
    assert (sub / "journey-analysis.md").is_file()
