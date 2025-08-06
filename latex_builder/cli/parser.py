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
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Repository path (positional argument)
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to the Git repository containing the LaTeX project (default: current directory)",
    )

    # Main LaTeX file
    parser.add_argument(
        "-f",
        "--tex-file",
        default="main.tex",
        help="Main LaTeX file to compile (default: main.tex)",
    )

    # LaTeX compiler choice
    parser.add_argument(
        "-c",
        "--compiler",
        choices=["xelatex", "pdflatex", "lualatex"],
        default="xelatex",
        help="LaTeX compiler to use (default: xelatex)",
    )

    # Comparison options
    parser.add_argument(
        "--compare-with",
        help="Compare with specific tag or commit hash (default: latest tag if available, otherwise previous commit)",
    )

    # Output options
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="Directory for output files (default: output)",
    )

    parser.add_argument(
        "-b",
        "--build-dir",
        default="build",
        help="Directory for build files (default: build)",
    )

    # Revision file path
    parser.add_argument(
        "--revision-file",
        default="miscellaneous/revision.tex",
        help="Path for generated revision.tex file (default: miscellaneous/revision.tex)",
    )

    # Build options
    parser.add_argument(
        "--no-diff",
        action="store_true",
        help="Only build current version, skip diff generation",
    )

    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Only generate diff, skip building PDFs",
    )

    # Logging
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress all output except errors"
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.no_diff and args.diff_only:
        parser.error("--no-diff and --diff-only are mutually exclusive")

    if args.verbose and args.quiet:
        parser.error("--verbose and --quiet are mutually exclusive")

    logger.info("Arguments parsed", **vars(args))

    return Config(
        repo_path=Path(args.repo_path).resolve(),
        tex_file=args.tex_file,
        compiler=args.compiler,
        compare_with=args.compare_with,
        revision_file=args.revision_file,
        output_dir=Path(args.output_dir),
        build_dir=Path(args.build_dir),
        no_diff=args.no_diff,
        diff_only=args.diff_only,
        verbose=args.verbose,
        quiet=args.quiet,
    )
