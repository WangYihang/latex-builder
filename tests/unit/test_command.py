"""Unit tests for latex_builder.utils.command."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from latex_builder.utils.command import run_command, run_latex_command


class TestRunCommand:
    """Test run_command function."""

    @patch("latex_builder.utils.command.subprocess.run")
    def test_successful_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        run_command(["echo", "hello"])
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["echo", "hello"]
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True

    @patch("latex_builder.utils.command.subprocess.run")
    def test_sets_latex_environment_variables(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        run_command(["echo", "test"])
        _, kwargs = mock_run.call_args
        assert kwargs["env"]["LATEX_INTERACTION"] == "batchmode"
        assert kwargs["env"]["TEXMFVAR"] == "/dev/null"

    @patch("latex_builder.utils.command.subprocess.run")
    def test_passes_cwd(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        cwd = Path("/tmp/test")
        run_command(["echo", "test"], cwd=cwd)
        _, kwargs = mock_run.call_args
        assert kwargs["cwd"] == cwd

    @patch("latex_builder.utils.command.subprocess.run")
    def test_passes_timeout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        run_command(["echo", "test"], timeout=60)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 60

    @patch("latex_builder.utils.command.subprocess.run")
    def test_default_timeout_is_300(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        run_command(["echo", "test"])
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 300

    @patch("latex_builder.utils.command.subprocess.run")
    def test_nonzero_exit_raises_runtime_error(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="some error output",
        )
        with pytest.raises(RuntimeError, match="Command failed.*exit code 1"):
            run_command(["false"])

    @patch("latex_builder.utils.command.subprocess.run")
    def test_nonzero_exit_includes_stderr(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=2,
            stderr="detailed error info",
        )
        with pytest.raises(RuntimeError, match="detailed error info"):
            run_command(["bad_cmd"])

    @patch("latex_builder.utils.command.subprocess.run")
    def test_empty_stderr_handled(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="")
        with pytest.raises(RuntimeError):
            run_command(["bad_cmd"])

    @patch("latex_builder.utils.command.subprocess.run")
    def test_timeout_raises_runtime_error(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="slow_cmd", timeout=10)
        with pytest.raises(RuntimeError, match="timed out"):
            run_command(["slow_cmd"], timeout=10)

    @patch("latex_builder.utils.command.subprocess.run")
    def test_stderr_truncated_to_500_chars(self, mock_run):
        long_stderr = "x" * 1000
        mock_run.return_value = MagicMock(returncode=1, stderr=long_stderr)
        with pytest.raises(RuntimeError) as exc_info:
            run_command(["bad_cmd"])
        # The error message should contain at most 500 chars of stderr
        assert "x" * 500 in str(exc_info.value)
        assert "x" * 501 not in str(exc_info.value)


class TestRunLatexCommand:
    """Test run_latex_command function."""

    @patch("latex_builder.utils.command.run_command")
    def test_adds_nonstopmode_to_xelatex(self, mock_run_cmd):
        run_latex_command(["xelatex", "main.tex"])
        called_cmd = mock_run_cmd.call_args[0][0]
        assert called_cmd == ["xelatex", "-interaction=nonstopmode", "main.tex"]

    @patch("latex_builder.utils.command.run_command")
    def test_adds_nonstopmode_to_pdflatex(self, mock_run_cmd):
        run_latex_command(["pdflatex", "main.tex"])
        called_cmd = mock_run_cmd.call_args[0][0]
        assert called_cmd == ["pdflatex", "-interaction=nonstopmode", "main.tex"]

    @patch("latex_builder.utils.command.run_command")
    def test_adds_nonstopmode_to_lualatex(self, mock_run_cmd):
        run_latex_command(["lualatex", "main.tex"])
        called_cmd = mock_run_cmd.call_args[0][0]
        assert called_cmd == ["lualatex", "-interaction=nonstopmode", "main.tex"]

    @patch("latex_builder.utils.command.run_command")
    def test_does_not_duplicate_nonstopmode(self, mock_run_cmd):
        run_latex_command(["xelatex", "-interaction=nonstopmode", "main.tex"])
        called_cmd = mock_run_cmd.call_args[0][0]
        assert called_cmd.count("-interaction=nonstopmode") == 1

    @patch("latex_builder.utils.command.run_command")
    def test_does_not_duplicate_batchmode(self, mock_run_cmd):
        run_latex_command(["xelatex", "-interaction=batchmode", "main.tex"])
        called_cmd = mock_run_cmd.call_args[0][0]
        assert "-interaction=nonstopmode" not in called_cmd

    @patch("latex_builder.utils.command.run_command")
    def test_does_not_add_to_non_latex_command(self, mock_run_cmd):
        run_latex_command(["bibtex", "main"])
        called_cmd = mock_run_cmd.call_args[0][0]
        assert "-interaction=nonstopmode" not in called_cmd

    @patch("latex_builder.utils.command.run_command")
    def test_does_not_modify_original_list(self, mock_run_cmd):
        original = ["xelatex", "main.tex"]
        original_copy = original.copy()
        run_latex_command(original)
        assert original == original_copy

    @patch("latex_builder.utils.command.run_command")
    def test_passes_cwd_and_timeout(self, mock_run_cmd):
        cwd = Path("/tmp")
        run_latex_command(["xelatex", "main.tex"], cwd=cwd, timeout=120)
        mock_run_cmd.assert_called_once()
        _, call_cwd, call_timeout = mock_run_cmd.call_args[0]
        assert call_cwd == cwd
        assert call_timeout == 120
