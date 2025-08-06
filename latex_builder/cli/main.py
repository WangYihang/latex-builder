"""Command line interface for LaTeX Builder."""

import os
import sys
import time

from latex_builder.config.settings import Config
from latex_builder.git.repository import GitRepository
from latex_builder.latex.processor import LaTeXProcessor
from latex_builder.diff.generator import DiffGenerator
from latex_builder.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


class LatexDiffTool:
    """Main application class for LaTeX diff tool."""
    
    def __init__(self, config: Config):
        """
        Initialize LatexDiffTool.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Set up logging
        setup_logging(config.verbose)
        
        # Initialize components
        logger.info("Initializing LaTeX Diff Tool")
        logger.info(f"Configuration:")
        logger.info(f"  • LaTeX file: {config.tex_file}")
        logger.info(f"  • Revision path: {config.revision_path}")
        logger.info(f"  • Output folder: {config.output_folder}")
        logger.info(f"  • Build directory: {config.build_dir}")
        logger.info(f"  • Verbose mode: {config.verbose}")
        
        self.git_repo = GitRepository()
        self.latex_processor = LaTeXProcessor()
        self.diff_generator = DiffGenerator(
            self.git_repo, 
            self.latex_processor,
            config
        )
    
    def run(self) -> int:
        """
        Execute the main workflow.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        start_time = time.time()
        logger.info("Starting LaTeX Diff Tool execution")
        
        try:
            # Get Git revisions
            current = self.git_repo.get_current_revision()
            previous_commit = self.git_repo.get_previous_commit()
            previous_tag = self.git_repo.get_previous_tag()
            
            if not previous_commit:
                logger.error("No previous commit found, cannot generate diff")
                return 1
            
            # Generate diffs
            logger.info("Starting diff generation process")
            self.diff_generator.generate_diffs(
                current,
                previous_commit,
                previous_tag
            )
            
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Process completed successfully in {duration:.2f} seconds")
            
            return 0
        except Exception as e:
            logger.error(f"An unexpected error occurred: {repr(e)}")
            return 1


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from latex_builder.cli.parser import parse_arguments
    
    logger.info("LaTeX Diff Tool starting")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    config = parse_arguments()
    tool = LatexDiffTool(config)
    
    logger.info("Running LaTeX Diff Tool")
    result = tool.run()
    
    if result == 0:
        logger.info("LaTeX Diff Tool completed successfully")
    else:
        logger.error("LaTeX Diff Tool failed")
    
    return result
