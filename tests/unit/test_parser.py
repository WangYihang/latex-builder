"""Unit tests for latex_builder.cli.parser.parse_arguments."""

import sys
from unittest.mock import patch

import pytest

from latex_builder.cli.parser import parse_arguments


class TestBuildSubcommand:
    """Test 'build' subcommand argument parsing."""

    def test_build_defaults(self):
        with patch("sys.argv", ["latex-builder", "build"]):
            args = parse_arguments()
        assert args.subcommand == "build"
        assert args.repo_path == "."
        assert args.tex_file == "main.tex"
        assert args.compiler == "xelatex"
        assert args.compare_with is None
        assert args.output_dir == "output"
        assert args.build_dir == "build"
        assert args.revision_file == "variables/revision.tex"
        assert args.no_diff is False
        assert args.diff_only is False
        assert args.verbose is False
        assert args.quiet is False

    def test_build_custom_repo_path(self):
        with patch("sys.argv", ["latex-builder", "build", "/my/repo"]):
            args = parse_arguments()
        assert args.repo_path == "/my/repo"

    def test_build_tex_file(self):
        with patch("sys.argv", ["latex-builder", "build", "-f", "thesis.tex"]):
            args = parse_arguments()
        assert args.tex_file == "thesis.tex"

    def test_build_compiler_pdflatex(self):
        with patch("sys.argv", ["latex-builder", "build", "-c", "pdflatex"]):
            args = parse_arguments()
        assert args.compiler == "pdflatex"

    def test_build_compiler_lualatex(self):
        with patch("sys.argv", ["latex-builder", "build", "-c", "lualatex"]):
            args = parse_arguments()
        assert args.compiler == "lualatex"

    def test_build_invalid_compiler_rejected(self):
        with patch("sys.argv", ["latex-builder", "build", "-c", "latexmk"]):
            with pytest.raises(SystemExit):
                parse_arguments()

    def test_build_compare_with(self):
        with patch("sys.argv", ["latex-builder", "build", "--compare-with", "v1.0.0"]):
            args = parse_arguments()
        assert args.compare_with == "v1.0.0"

    def test_build_output_dir(self):
        with patch("sys.argv", ["latex-builder", "build", "-o", "dist"]):
            args = parse_arguments()
        assert args.output_dir == "dist"

    def test_build_build_dir(self):
        with patch("sys.argv", ["latex-builder", "build", "-b", "tmp_build"]):
            args = parse_arguments()
        assert args.build_dir == "tmp_build"

    def test_build_no_diff_flag(self):
        with patch("sys.argv", ["latex-builder", "build", "--no-diff"]):
            args = parse_arguments()
        assert args.no_diff is True

    def test_build_diff_only_flag(self):
        with patch("sys.argv", ["latex-builder", "build", "--diff-only"]):
            args = parse_arguments()
        assert args.diff_only is True

    def test_build_verbose_flag(self):
        with patch("sys.argv", ["latex-builder", "build", "-v"]):
            args = parse_arguments()
        assert args.verbose is True

    def test_build_quiet_flag(self):
        with patch("sys.argv", ["latex-builder", "build", "-q"]):
            args = parse_arguments()
        assert args.quiet is True

    def test_build_multiple_flags(self):
        with patch("sys.argv", ["latex-builder", "build", "--no-diff", "-v", "-f", "paper.tex"]):
            args = parse_arguments()
        assert args.no_diff is True
        assert args.verbose is True
        assert args.tex_file == "paper.tex"


class TestRevisionSubcommand:
    """Test 'revision' subcommand argument parsing."""

    def test_revision_defaults(self):
        with patch("sys.argv", ["latex-builder", "revision"]):
            args = parse_arguments()
        assert args.subcommand == "revision"
        assert args.repo_path == "."
        assert args.revision_file == "variables/revision.tex"

    def test_revision_custom_repo_path(self):
        with patch("sys.argv", ["latex-builder", "revision", "/my/repo"]):
            args = parse_arguments()
        assert args.repo_path == "/my/repo"

    def test_revision_custom_file(self):
        with patch("sys.argv", ["latex-builder", "revision", "--revision-file", "version.tex"]):
            args = parse_arguments()
        assert args.revision_file == "version.tex"

    def test_revision_verbose(self):
        with patch("sys.argv", ["latex-builder", "revision", "-v"]):
            args = parse_arguments()
        assert args.verbose is True

    def test_revision_quiet(self):
        with patch("sys.argv", ["latex-builder", "revision", "-q"]):
            args = parse_arguments()
        assert args.quiet is True


class TestNoSubcommand:
    """Test behavior when no subcommand is specified."""

    def test_no_subcommand_sets_none(self):
        with patch("sys.argv", ["latex-builder"]):
            args = parse_arguments()
        assert args.subcommand is None
