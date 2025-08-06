"""Configuration management for LaTeX Builder."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Configuration for the LaTeX diff tool."""
    repo_path: Path = Path(".")
    tex_file: str = "main.tex"
    compiler: str = "xelatex"
    compare_with: Optional[str] = None
    revision_file: str = "miscellaneous/revision.tex"
    output_dir: Path = Path("output")
    build_dir: Path = Path("build")
    no_diff: bool = False
    diff_only: bool = False
    verbose: bool = False
    quiet: bool = False
    
    def __post_init__(self):
        """Ensure Path objects are properly initialized."""
        if isinstance(self.repo_path, str):
            self.repo_path = Path(self.repo_path).resolve()
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.build_dir, str):
            self.build_dir = Path(self.build_dir)
    
    @property 
    def revision_path(self) -> str:
        """Legacy property for backward compatibility."""
        return self.revision_file
