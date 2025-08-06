"""Command line argument parsing."""

import argparse
from pathlib import Path

from latex_builder.config.settings import Config
from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


def parse_arguments() -> Config:
    """Parse command line arguments.
    
    Returns:
        Config object with parsed arguments
    """
    logger.info("Parsing command line arguments")
    
    parser = argparse.ArgumentParser(
        description="LaTeX build and diff tool for Git repositories",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "-t", "--tex-file", 
        default="main.tex", 
        help="Main LaTeX file to compile"
    )
    
    parser.add_argument(
        "-r", "--revision-path", 
        default="miscellaneous/revision.tex", 
        help="Path for revision.tex"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "-o", "--output-folder",
        default="output",
        help="Folder for output files"
    )
    
    parser.add_argument(
        "-b", "--build-dir",
        default="build",
        help="Directory for build files"
    )
    
    args = parser.parse_args()
    logger.info("Arguments parsed", **vars(args))
    
    return Config(
        tex_file=args.tex_file,
        revision_path=args.revision_path,
        verbose=args.verbose,
        output_folder=Path(args.output_folder),
        build_dir=Path(args.build_dir)
    )
