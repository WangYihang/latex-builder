"""LaTeX Builder — build LaTeX documents with Git integration and diff generation."""

__version__ = "0.1.0"
__repo_url__ = "https://github.com/WangYihang/latex-builder"
__author_github__ = "WangYihang"

from latex_builder.config import Compiler, Config
from latex_builder.revision import Revision
from latex_builder.git import GitRepo

__all__ = ["Compiler", "Config", "Revision", "GitRepo", "__version__"]
