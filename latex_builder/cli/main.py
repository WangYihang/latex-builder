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
        """Initialize LatexDiffTool.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        setup_logging(config.verbose)
        
        logger.info("Initializing LaTeX Diff Tool", 
                   tex_file=config.tex_file,
                   revision_path=config.revision_path,
                   output_folder=str(config.output_folder),
                   build_dir=str(config.build_dir),
                   verbose=config.verbose)
        
        self.git_repo = GitRepository()
        self.latex_processor = LaTeXProcessor()
        self.diff_generator = DiffGenerator(
            self.git_repo, 
            self.latex_processor,
            config
        )
    
    def run(self) -> int:
        """Execute the main workflow.
        
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
            
            if not previous_tag:
                logger.error("No previous tag found, cannot generate diff")
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
            logger.info("Process completed successfully", duration=f"{duration:.2f}s")
            
            return 0
        except Exception as e:
            logger.error("Unexpected error occurred", error=str(e))
            return 1


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from latex_builder.cli.parser import parse_arguments
    
    logger.info("LaTeX Diff Tool starting", 
               python_version=sys.version,
               working_dir=os.getcwd())
    
    config = parse_arguments()
    tool = LatexDiffTool(config)
    
    logger.info("Running LaTeX Diff Tool")
    result = tool.run()
    
    if result == 0:
        logger.info("LaTeX Diff Tool completed successfully")
    else:
        logger.error("LaTeX Diff Tool failed", exit_code=result)
    
    return result
