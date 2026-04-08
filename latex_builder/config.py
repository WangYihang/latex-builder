"""Configuration and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

SUPPORTED_COMPILERS = ("xelatex", "pdflatex", "lualatex")


class Compiler(str, Enum):
    XELATEX = "xelatex"
    PDFLATEX = "pdflatex"
    LUALATEX = "lualatex"


@dataclass(frozen=True)
class Config:
    """Immutable build configuration."""

    repo_path: Path = field(default_factory=Path.cwd)
    tex_file: str = "main.tex"
    compiler: Compiler = Compiler.XELATEX
    compare_with: str | None = None
    revision_file: str = "variables/revision.tex"
    output_dir: Path = Path("output")
    build_dir: Path = Path("build")
    timeout: int = 300
    skip_diff: bool = False
    diff_only: bool = False
    verbose: bool = False
    quiet: bool = False
