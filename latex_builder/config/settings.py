"""Configuration management for LaTeX Builder."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration for the LaTeX diff tool."""
    tex_file: str = "main.tex"
    revision_path: str = "miscellaneous/revision.tex"
    verbose: bool = False
    output_folder: Path = Path("output")
    build_dir: Path = Path("build")
    
    def __post_init__(self):
        """Ensure Path objects are properly initialized."""
        if isinstance(self.output_folder, str):
            self.output_folder = Path(self.output_folder)
        if isinstance(self.build_dir, str):
            self.build_dir = Path(self.build_dir)
