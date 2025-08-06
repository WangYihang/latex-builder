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

        # Setup logging with quiet/verbose options
        if config.quiet:
            setup_logging(verbose=False, quiet=True)
        else:
            setup_logging(config.verbose)

        logger.info(
            "Initializing LaTeX Diff Tool",
            repo_path=str(config.repo_path),
            tex_file=config.tex_file,
            compiler=config.compiler,
            compare_with=config.compare_with,
            revision_file=config.revision_file,
            output_dir=str(config.output_dir),
            build_dir=str(config.build_dir),
            no_diff=config.no_diff,
            diff_only=config.diff_only,
            verbose=config.verbose,
            quiet=config.quiet,
        )

        self.git_repo = GitRepository(config.repo_path)
        self.latex_processor = LaTeXProcessor(config.repo_path)
        self.diff_generator = DiffGenerator(self.git_repo, self.latex_processor, config)

    def run(self) -> int:
        """Execute the main workflow.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        start_time = time.time()
        logger.info("Starting LaTeX Diff Tool execution")

        try:
            # Check if LaTeX file exists
            tex_path = self.config.repo_path / self.config.tex_file
            if not tex_path.exists():
                logger.error(f"LaTeX file not found: {tex_path}")
                return 1

            # Get current Git revision
            current = self.git_repo.get_current_revision()

            # Determine comparison target
            compare_revision = None
            if self.config.compare_with:
                logger.info(
                    f"Using specified comparison target: {self.config.compare_with}"
                )
                compare_revision = self.git_repo.get_revision_by_ref(
                    self.config.compare_with
                )
                if not compare_revision:
                    logger.error(
                        f"Comparison target not found: {self.config.compare_with}"
                    )
                    return 1
            else:
                # Auto-select comparison target: latest tag or previous commit
                logger.info("Auto-selecting comparison target")
                compare_revision = self.git_repo.get_previous_tag()
                if not compare_revision:
                    logger.info("No tags found, using previous commit")
                    compare_revision = self.git_repo.get_previous_commit()
                    if not compare_revision:
                        logger.error("No previous commit found, cannot generate diff")
                        return 1

            if self.config.diff_only:
                logger.info("Diff-only mode: generating diff without building PDFs")
                self.diff_generator.generate_diff_only(current, compare_revision)
            elif self.config.no_diff:
                logger.info("No-diff mode: building current version only")
                self.diff_generator.build_current_only(current)
            else:
                logger.info("Full mode: building PDFs and generating diff")
                self.diff_generator.generate_diffs(current, compare_revision)

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

    logger.info(
        "LaTeX Diff Tool starting", python_version=sys.version, working_dir=os.getcwd()
    )

    config = parse_arguments()
    tool = LatexDiffTool(config)

    logger.info("Running LaTeX Diff Tool")
    result = tool.run()

    if result == 0:
        logger.info("LaTeX Diff Tool completed successfully")
    else:
        logger.error("LaTeX Diff Tool failed", exit_code=result)

    return result
