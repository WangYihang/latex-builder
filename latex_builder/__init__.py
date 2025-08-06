"""LaTeX Builder - A tool for building LaTeX documents with Git integration."""

__version__ = "0.1.0"

from .config.settings import Config
from .git.revision import GitRevision
from .git.repository import GitRepository
from .latex.processor import LaTeXProcessor
from .diff.generator import DiffGenerator
from .cli.main import LatexDiffTool

__all__ = [
    "Config",
    "GitRevision",
    "GitRepository",
    "LaTeXProcessor",
    "DiffGenerator",
    "LatexDiffTool",
]
