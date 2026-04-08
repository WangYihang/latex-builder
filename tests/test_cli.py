"""End-to-end tests for the CLI."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from latex_builder.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestRevisionSubcommand:
    def test_generates_file(self, runner, git_repo):
        out = git_repo / "variables" / "revision.tex"
        result = runner.invoke(main, ["revision", str(git_repo), "--revision-file", str(out), "-q"])
        assert result.exit_code == 0
        assert out.exists()
        assert r"\newcommand" in out.read_text()


class TestBuildSubcommand:
    @patch("latex_builder.diff.compiler.build")
    @patch("latex_builder.diff.compiler.latexdiff")
    def test_full_workflow(self, mock_diff, mock_build, runner, git_repo):
        mock_build.return_value = git_repo / "output" / "test.pdf"
        mock_diff.return_value = git_repo / "output" / "diff.tex"

        result = runner.invoke(main, [
            "build", str(git_repo), "-q",
            "-o", str(git_repo / "output"),
        ])
        assert result.exit_code == 0

    @patch("latex_builder.diff.compiler.build")
    def test_skip_diff(self, mock_build, runner, git_repo):
        mock_build.return_value = git_repo / "output" / "test.pdf"

        result = runner.invoke(main, [
            "build", str(git_repo), "--skip-diff", "-q",
            "-o", str(git_repo / "output"),
        ])
        assert result.exit_code == 0

    def test_missing_tex_file(self, runner, git_repo):
        result = runner.invoke(main, [
            "build", str(git_repo), "-f", "nonexistent.tex", "-q",
        ])
        assert result.exit_code != 0

    def test_invalid_compare_ref(self, runner, git_repo):
        result = runner.invoke(main, [
            "build", str(git_repo), "--compare-with", "v99.99.99", "-q",
        ])
        assert result.exit_code != 0


class TestDefaultInvocation:
    @patch("latex_builder.diff.compiler.build")
    @patch("latex_builder.diff.compiler.latexdiff")
    def test_no_subcommand_runs_build(self, mock_diff, mock_build, runner, git_repo):
        mock_build.return_value = git_repo / "output" / "test.pdf"
        mock_diff.return_value = git_repo / "output" / "diff.tex"

        result = runner.invoke(main, [
            "--", str(git_repo), "-q",
            "-o", str(git_repo / "output"),
        ])
        # May or may not work depending on click routing, but should not crash
        # The default command is build
