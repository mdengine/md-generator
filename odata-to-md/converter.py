"""Shim CLI: prefer ``md-odata`` after ``pip install mdengine[odata]``."""

from __future__ import annotations

import sys


def main() -> None:
    from md_generator.odata.cli.main import main as _main

    raise SystemExit(_main(sys.argv[1:]))


if __name__ == "__main__":
    main()
