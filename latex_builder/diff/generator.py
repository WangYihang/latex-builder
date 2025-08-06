"""Diff generation functionality for LaTeX documents."""

import json
import datetime
from pathlib import Path
from typing import Dict

from latex_builder.git.repository import GitRepository
from latex_builder.git.revision import GitRevision
from latex_builder.latex.processor import LaTeXProcessor
from latex_builder.config.settings import Config
from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


class DiffGenerator:
    """Handles the generation of LaTeX diffs between Git revisions."""
    
    def __init__(self, 
                git_repo: GitRepository, 
                latex_processor: LaTeXProcessor,
                config: Config):
        """
        Initialize DiffGenerator.
        
        Args:
            git_repo: GitRepository instance
            latex_processor: LaTeXProcessor instance
            config: Configuration object
        """
        self.git_repo = git_repo
        self.latex_processor = latex_processor
        self.config = config
        self.output_folder = config.output_dir
        self.build_dir = config.build_dir
        
        logger.info("Diff generator initialized",
                   output_folder=str(self.output_folder),
                   build_dir=str(self.build_dir))
    
    def generate_diffs(self, 
                      current: GitRevision, 
                      compare_revision: GitRevision) -> None:
        """
        Generate and build diff files between Git revisions.
        
        Args:
            current: Current Git revision
            compare_revision: Revision to compare against
            
        Raises:
            RuntimeError: If any operation fails
        """
        logger.info("Starting diff generation process",
                   current=current.display_name,
                   compare_with=compare_revision.display_name)
        
        if not self.output_folder.exists():
            logger.info("Creating output folder", path=str(self.output_folder))
            self.output_folder.mkdir(parents=True, exist_ok=True)

        if not self.build_dir.exists():
            logger.info("Creating build directory", path=str(self.build_dir))
            self.build_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Build the current version first
            logger.info(f"  • Building current version")
            self._build_current_version(current)
        except Exception as e:
            logger.error(f"  • Failed to build current version: {repr(e)}")

        try:
            # Generate and build diff files
            logger.info(f"  • Generating and building diff files")
            self._generate_and_build_diff(current, compare_revision)
        except Exception as e:
            logger.error(f"  • Failed to generate and build diff: {repr(e)}")
        
        # Save metadata
        logger.info(f"  • Saving metadata")
        self._save_metadata(current, compare_revision)
        
        logger.info("Diff generation completed successfully")
    
    def build_current_only(self, current: GitRevision) -> None:
        """
        Build only the current version without generating diff.
        
        Args:
            current: Current Git revision
        """
        logger.info("Building current version only", current=current.display_name)
        
        if not self.output_folder.exists():
            logger.info("Creating output folder", path=str(self.output_folder))
            self.output_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            self._build_current_version(current)
            logger.info("Current version build completed successfully")
        except Exception as e:
            logger.error(f"Failed to build current version: {repr(e)}")
            raise
    
    def generate_diff_only(self, current: GitRevision, compare_revision: GitRevision) -> None:
        """
        Generate only the diff file without building PDFs.
        
        Args:
            current: Current Git revision
            compare_revision: Revision to compare against
        """
        logger.info("Generating diff only", 
                   current=current.display_name,
                   compare_with=compare_revision.display_name)
        
        if not self.output_folder.exists():
            logger.info("Creating output folder", path=str(self.output_folder))
            self.output_folder.mkdir(parents=True, exist_ok=True)
        
        if not self.build_dir.exists():
            logger.info("Creating build directory", path=str(self.build_dir))
            self.build_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Setup checkout directories
            checkout_dirs = self._prepare_checkout_directories(current, compare_revision)
            
            # Generate diff file
            diff_name = f"diff-{compare_revision.short_hash}-{current.short_hash}.tex"
            logger.info(f"Generating diff file: {diff_name}")
            
            self.latex_processor.generate_diff(
                checkout_dirs["compare"] / self.config.tex_file,
                checkout_dirs["current"] / self.config.tex_file,
                self.output_folder / diff_name
            )
            
            logger.info("Diff file generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate diff: {repr(e)}")
            raise
    
    def _build_current_version(self, current: GitRevision) -> None:
        """
        Build the current version of the LaTeX document.
        
        Args:
            current: Current Git revision
        """
        logger.info(f"  • Building current version: {current.display_name}")
        original_dir = self.config.repo_path
        logger.info(f"    - Working directory: {original_dir}")

        # Generate revision file in the repo
        revision_file_path = original_dir / self.config.revision_file
        logger.info(f"    - Generating revision file at: {revision_file_path}")
        self.git_repo.generate_revision_file(current, revision_file_path)

        # Build document
        logger.info(f"    - Building LaTeX document")
        self.latex_processor.build_document(
            self.config.tex_file, 
            original_dir, 
            self.output_folder, 
            f"{current.display_name}.pdf",
            self.config.compiler
        )
        logger.info(f"    - Current version build completed")
    
    def _prepare_checkout_directories(self, 
                                     current: GitRevision, 
                                     compare_revision: GitRevision) -> Dict[str, Path]:
        """
        Prepare directories for checking out different Git revisions.
        
        Args:
            current: Current Git revision
            compare_revision: Revision to compare against
            
        Returns:
            Dictionary mapping revision names to checkout directories
        """
        # Setup checkout directories
        current_dir = self.build_dir / "current"
        compare_dir = self.build_dir / "compare"
        
        logger.info(f"    - Current directory: {current_dir}")
        logger.info(f"    - Compare directory: {compare_dir}")
        
        # Checkout all needed revisions
        logger.info(f"    - Checking out current revision: {current.display_name}")
        self.git_repo.checkout_revision(current, current_dir)
        
        logger.info(f"    - Checking out compare revision: {compare_revision.display_name}")
        self.git_repo.checkout_revision(compare_revision, compare_dir)
        
        logger.info(f"    - All revisions checked out successfully")
        
        return {
            "current": current_dir,
            "compare": compare_dir
        }
    
    def _generate_and_build_diff(self, 
                                 current: GitRevision, 
                                 compare_revision: GitRevision) -> None:
        """
        Generate and build diff files.
        
        Args:
            current: Current Git revision
            compare_revision: Revision to compare against
        """
        # Setup checkout directories
        checkout_dirs = self._prepare_checkout_directories(current, compare_revision)
        
        # Generate diff file name
        diff_name = f"diff-{compare_revision.short_hash}-{current.short_hash}.tex"
        logger.info(f"    - Diff filename: {diff_name}")

        # Generate diff
        logger.info(f"    - Generating diff from {compare_revision.display_name} to {current.display_name}")
        self.latex_processor.generate_diff(
            checkout_dirs["compare"] / self.config.tex_file,
            checkout_dirs["current"] / self.config.tex_file,
            checkout_dirs["compare"] / diff_name
        )
        
        # Build diff document
        logger.info(f"    - Building diff document")
        diff_pdf_name = f"diff-{compare_revision.display_name}-to-{current.display_name}.pdf"
        self.latex_processor.build_document(
            diff_name, 
            checkout_dirs["compare"], 
            self.output_folder, 
            diff_pdf_name,
            self.config.compiler
        )
        
        logger.info(f"    - Diff document built successfully")
    
    def _save_metadata(self, 
                      current: GitRevision, 
                      compare_revision: GitRevision) -> None:
        """
        Save metadata about the diff generation.
        
        Args:
            current: Current Git revision
            compare_revision: Revision compared against
        """
        metadata = {
            "current_commit": current.short_hash,
            "current_display_name": current.display_name,
            "compare_commit": compare_revision.short_hash,
            "compare_display_name": compare_revision.display_name,
            "compare_tag": compare_revision.tag_name,
            "tex_file": self.config.tex_file,
            "compiler": self.config.compiler,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"    - Creating metadata:")
        for key, value in metadata.items():
            logger.info(f"      • {key}: {value}")
        
        metadata_file = self.output_folder / "metadata.json"
        logger.info(f"    - Writing metadata to: {metadata_file}")
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)
        
        logger.info(f"    - Metadata saved successfully")
