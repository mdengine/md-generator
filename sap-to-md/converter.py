"""Shim CLI: prefer ``md-sap`` after ``pip install mdengine[sap]``."""

from __future__ import annotations

import sys


def main() -> None:
    from md_generator.sap.cli.main import main as _main

    raise SystemExit(_main(sys.argv[1:]))


if __name__ == "__main__":
    main()
