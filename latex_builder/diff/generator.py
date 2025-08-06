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
        self.output_folder = config.output_folder
        self.build_dir = config.build_dir
        
        logger.info("Diff generator initialized",
                   output_folder=str(self.output_folder),
                   build_dir=str(self.build_dir))
    
    def generate_diffs(self, 
                      current: GitRevision, 
                      previous_commit: GitRevision, 
                      previous_tag: GitRevision) -> None:
        """
        Generate and build diff files between Git revisions.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
            
        Raises:
            RuntimeError: If any operation fails
        """
        logger.info("Starting diff generation process",
                   current=current.display_name,
                   previous_commit=previous_commit.display_name,
                   previous_tag=previous_tag.display_name)
        
        if not self.output_folder.exists():
            logger.info("Creating output folder", path=str(self.output_folder))
            self.output_folder.mkdir(parents=True, exist_ok=True)

        if not self.build_dir.exists():
            logger.info("Creating build directory", path=str(self.build_dir))
            self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup checkout directories
        logger.info(f"  • Setting up checkout directories")
        checkout_dirs = self._prepare_checkout_directories(current, previous_commit, previous_tag)

        try:
            # Build the current version first
            logger.info(f"  • Building current version")
            self._build_current_version(current, checkout_dirs["current"])
        except Exception as e:
            logger.error(f"  • Failed to build current version: {repr(e)}")

        try:

            # Generate and build diff files
            logger.info(f"  • Generating and building diff files")
            self._generate_and_build_diffs(current, previous_commit, previous_tag, checkout_dirs)
        except Exception as e:
            logger.error(f"  • Failed to generate and build diffs: {repr(e)}")
        
        # Save metadata
        logger.info(f"  • Saving metadata")
        self._save_metadata(current, previous_commit, previous_tag)
        
        logger.info("Diff generation completed successfully")
    
    def _build_current_version(self, current: GitRevision, current_dir: Path) -> None:
        """
        Build the current version of the LaTeX document.
        
        Args:
            current: Current Git revision
            current_dir: Path to the directory for the current revision
        """
        logger.info(f"  • Building current version: {current.display_name}")
        original_dir = Path.cwd()
        logger.info(f"    - Current working directory: {original_dir}")

        # Generate revision file
        revision_file_path = current_dir / self.config.revision_path
        logger.info(f"    - Generating revision file at: {revision_file_path}")
        self.git_repo.generate_revision_file(
            current, 
            revision_file_path,
        )

        logger.info(f"    - Generating revision file at: {revision_file_path}")
        self.git_repo.generate_revision_file(
            current, 
            Path(self.config.revision_path),
        )

        # Build document
        logger.info(f"    - Building LaTeX document")
        self.latex_processor.build_document(
            self.config.tex_file, 
            original_dir, 
            self.output_folder, 
            f"{current.display_name}.pdf"
        )
        logger.info(f"    - Current version build completed")
    
    def _prepare_checkout_directories(self, 
                                     current: GitRevision, 
                                     previous_commit: GitRevision, 
                                     previous_tag: GitRevision) -> Dict[str, Path]:
        """
        Prepare directories for checking out different Git revisions.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
            
        Returns:
            Dictionary mapping revision names to checkout directories
        """
        # Setup checkout directories
        current_commit_dir = self.build_dir / "current_commit"
        previous_commit_dir = self.build_dir / "previous_commit"
        previous_tag_dir = self.build_dir / "previous_tag"
        
        logger.info(f"    - Current commit directory: {current_commit_dir}")
        logger.info(f"    - Previous commit directory: {previous_commit_dir}")
        logger.info(f"    - Previous tag directory: {previous_tag_dir}")
        
        # Checkout all needed revisions
        logger.info(f"    - Checking out current revision: {current.display_name}")
        self.git_repo.checkout_revision(current, current_commit_dir)
        
        logger.info(f"    - Checking out previous commit: {previous_commit.display_name}")
        self.git_repo.checkout_revision(previous_commit, previous_commit_dir)
        
        logger.info(f"    - Checking out previous tag: {previous_tag.display_name}")
        self.git_repo.checkout_revision(previous_tag, previous_tag_dir)
        
        logger.info(f"    - All revisions checked out successfully")
        
        return {
            "current": current_commit_dir,
            "previous_commit": previous_commit_dir,
            "previous_tag": previous_tag_dir
        }
    
    def _generate_and_build_diffs(self, 
                                 current: GitRevision, 
                                 previous_commit: GitRevision, 
                                 previous_tag: GitRevision,
                                 checkout_dirs: Dict[str, Path]) -> None:
        """
        Generate and build diff files.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
            checkout_dirs: Dictionary mapping revision names to checkout directories
        """
        # Generate diff file names
        tag_diff_name = f"diff-{previous_tag.short_hash}-{current.short_hash}.tex"
        commit_diff_name = f"diff-{previous_commit.short_hash}-{current.short_hash}.tex"
        
        logger.info(f"    - Tag diff filename: {tag_diff_name}")
        logger.info(f"    - Commit diff filename: {commit_diff_name}")

        # Generate tag diff
        logger.info(f"    - Generating diff since last tag")
        self.latex_processor.generate_diff(
            checkout_dirs["previous_tag"] / self.config.tex_file,
            checkout_dirs["current"] / self.config.tex_file,
            checkout_dirs["previous_tag"] / tag_diff_name
        )
        
        # Generate commit diff
        logger.info(f"    - Generating diff since last commit")
        self.latex_processor.generate_diff(
            checkout_dirs["previous_commit"] / self.config.tex_file,
            checkout_dirs["current"] / self.config.tex_file,
            checkout_dirs["previous_commit"] / commit_diff_name
        )
        
        # Build tag diff document
        logger.info(f"    - Building tag diff document")
        self.latex_processor.build_document(
            tag_diff_name, 
            checkout_dirs["previous_tag"], 
            self.output_folder / "diff", 
            f"since-last-tag-{previous_tag.display_name}.pdf"
        )
        
        # Build commit diff document
        logger.info(f"    - Building commit diff document")
        self.latex_processor.build_document(
            commit_diff_name, 
            checkout_dirs["previous_commit"], 
            self.output_folder / "diff", 
            f"since-last-commit-{previous_commit.short_hash}.pdf"
        )
        
        logger.info(f"    - All diff documents built successfully")
    
    def _save_metadata(self, 
                      current: GitRevision, 
                      previous_commit: GitRevision, 
                      previous_tag: GitRevision) -> None:
        """
        Save metadata about the diff generation.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
        """
        metadata = {
            "current_commit": current.short_hash,
            "current_display_name": current.display_name,
            "previous_commit": previous_commit.short_hash,
            "previous_commit_display_name": previous_commit.display_name,
            "previous_tag": previous_tag.tag_name or previous_tag.short_hash,
            "previous_tag_display_name": previous_tag.display_name,
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
