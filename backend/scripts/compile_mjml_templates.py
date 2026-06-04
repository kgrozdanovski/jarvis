#!/usr/bin/env python3
"""
Compile MJML email templates to HTML once (for build pipelines or local dev).

Usage:
  MJML_BINARY=/path/to/mjml python scripts/compile_mjml_templates.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "src" / "templates" / "email"
MJML_BINARY = os.getenv("MJML_BINARY", "mjml")


class MJMLCompileError(Exception):
    """Raised when MJML compilation fails."""


def compile_template(path: Path) -> Path:
    """Compile a single MJML file to HTML, preserving Jinja placeholders."""
    output_path = path.with_suffix(".compiled.html")
    try:
        result = subprocess.run(
            [MJML_BINARY, str(path), "-o", str(output_path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise MJMLCompileError(f"MJML binary '{MJML_BINARY}' not found") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise MJMLCompileError(f"MJML failed for {path.name}: {stderr or exc}") from exc

    stdout = (result.stdout or "").strip()
    if stdout:
        print(stdout)

    return output_path


def main() -> int:
    if not TEMPLATE_DIR.exists():
        print(f"Template directory not found: {TEMPLATE_DIR}", file=sys.stderr)
        return 1

    mjml_files = sorted(TEMPLATE_DIR.glob("*.mjml"))
    if not mjml_files:
        print(f"No MJML templates found in {TEMPLATE_DIR}")
        return 0

    print(f"Compiling {len(mjml_files)} MJML template(s) with '{MJML_BINARY}'...")
    for template in mjml_files:
        output = compile_template(template)
        print(f"  ✔ {template.name} -> {output.name}")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
