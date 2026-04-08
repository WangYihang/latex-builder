"""Tests for latex_builder.shell."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from latex_builder.shell import run, run_latex


class TestRun:
    @patch("latex_builder.shell.subprocess.run")
    def test_success(self, mock_sub):
        mock_sub.return_value = MagicMock(returncode=0, stderr="")
        run(["echo", "hi"])
        mock_sub.assert_called_once()

    @patch("latex_builder.shell.subprocess.run")
    def test_sets_env(self, mock_sub):
        mock_sub.return_value = MagicMock(returncode=0, stderr="")
        run(["echo"])
        env = mock_sub.call_args.kwargs["env"]
        assert env["LATEX_INTERACTION"] == "batchmode"

    @patch("latex_builder.shell.subprocess.run")
    def test_nonzero_raises(self, mock_sub):
        mock_sub.return_value = MagicMock(returncode=1, stderr="err")
        with pytest.raises(RuntimeError, match="exit 1"):
            run(["false"])

    @patch("latex_builder.shell.subprocess.run")
    def test_timeout_raises(self, mock_sub):
        mock_sub.side_effect = subprocess.TimeoutExpired("cmd", 5)
        with pytest.raises(RuntimeError, match="timed out"):
            run(["slow"], timeout=5)

    @patch("latex_builder.shell.subprocess.run")
    def test_check_false_allows_nonzero(self, mock_sub):
        mock_sub.return_value = MagicMock(returncode=1, stderr="")
        result = run(["bad"], check=False)
        assert result.returncode == 1


class TestRunLatex:
    @patch("latex_builder.shell.run")
    def test_injects_nonstopmode(self, mock_run):
        run_latex(["xelatex", "main.tex"])
        cmd = mock_run.call_args.args[0]
        assert cmd == ["xelatex", "-interaction=nonstopmode", "main.tex"]

    @patch("latex_builder.shell.run")
    def test_no_duplicate_flag(self, mock_run):
        run_latex(["xelatex", "-interaction=batchmode", "main.tex"])
        cmd = mock_run.call_args.args[0]
        assert "-interaction=nonstopmode" not in cmd

    @patch("latex_builder.shell.run")
    def test_non_latex_unchanged(self, mock_run):
        run_latex(["bibtex", "main"])
        cmd = mock_run.call_args.args[0]
        assert "-interaction=nonstopmode" not in cmd

    @patch("latex_builder.shell.run")
    def test_does_not_mutate_input(self, mock_run):
        original = ["xelatex", "main.tex"]
        run_latex(original)
        assert original == ["xelatex", "main.tex"]
