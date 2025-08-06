"""Command line interface."""

from .main import LatexDiffTool, main
from .parser import parse_arguments

__all__ = ["LatexDiffTool", "main", "parse_arguments"]
