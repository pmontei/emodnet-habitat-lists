"""Text extraction from PDF sources with poppler's ``pdftotext``.

``pdftotext`` (poppler-utils) is a system dependency: ``apt install poppler-utils``,
``conda install -c conda-forge poppler`` or, on Windows, the poppler binaries on PATH.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def available() -> bool:
    return shutil.which("pdftotext") is not None


def pdf_to_lines(pdf: Path, layout: bool = True) -> list[str]:
    """Return the text of ``pdf`` as a list of lines (``-layout`` keeps indentation)."""
    if not available():
        raise RuntimeError("pdftotext (poppler-utils) is required to read PDF sources")
    args = ["pdftotext", "-enc", "UTF-8"]
    if layout:
        args.append("-layout")
    args += [str(pdf), "-"]
    out = subprocess.run(args, check=True, capture_output=True)
    return out.stdout.decode("utf-8", errors="replace").split("\n")
