"""Command line argument parsing."""

import argparse

from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments and handle subcommands.
    Returns:
        argparse.Namespace with parsed arguments (not Config)
    """
    logger.info("Parsing command line arguments")

    parser = argparse.ArgumentParser(
        description="LaTeX build and diff tool for Git repositories",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=False)

    # Main build/diff command (default)
    main_parser = subparsers.add_parser(
        "build", help="Build and diff LaTeX project (default)"
    )
    main_parser.add_argument(
        "repo_path", nargs="?", default=".",
        help="Path to the Git repository containing the LaTeX project (default: current directory)",
    )
    main_parser.add_argument(
        "-f", "--tex-file", default="main.tex",
        help="Main LaTeX file to compile (default: main.tex)"
    )
    main_parser.add_argument(
        "-c", "--compiler",
        choices=["xelatex", "pdflatex", "lualatex"],
        default="xelatex",
        help="LaTeX compiler to use (default: xelatex)"
    )
    main_parser.add_argument(
        "--compare-with",
        help="Compare with specific tag or commit hash (default: latest tag if available, otherwise previous commit)"
    )
    main_parser.add_argument(
        "-o", "--output-dir", default="output",
        help="Directory for output files (default: output)"
    )
    main_parser.add_argument(
        "-b", "--build-dir", default="build",
        help="Directory for build files (default: build)"
    )
    main_parser.add_argument(
        "--revision-file", default="variables/revision.tex",
        help="Path for generated revision.tex file (default: variables/revision.tex)"
    )
    main_parser.add_argument(
        "--no-diff", action="store_true",
        help="Only build current version, skip diff generation"
    )
    main_parser.add_argument(
        "--diff-only", action="store_true",
        help="Only generate diff, skip building PDFs"
    )
    main_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging"
    )
    main_parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress all output except errors"
    )

    # Revision subcommand
    revision_parser = subparsers.add_parser(
        "revision", help="Generate only revision.tex file"
    )
    revision_parser.add_argument(
        "repo_path", nargs="?", default=".",
        help="Path to the Git repository containing the LaTeX project (default: current directory)"
    )
    revision_parser.add_argument(
        "--revision-file", default="variables/revision.tex",
        help="Path for generated revision.tex file (default: variables/revision.tex)"
    )
    revision_parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose logging"
    )
    revision_parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress all output except errors"
    )

    args = parser.parse_args()
    logger.info("Arguments parsed", **vars(args))
    return args
