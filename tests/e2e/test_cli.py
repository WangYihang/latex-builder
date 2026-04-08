"""End-to-end tests for the latex-builder CLI.

These tests exercise the full workflow from CLI arguments through to output files.
LaTeX compilation is mocked since texlive may not be available in test environments.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from latex_builder.cli.main import LatexDiffTool, main
from latex_builder.config.settings import Config


class TestFullWorkflowNoDiff:
    """Test full workflow in no-diff mode (build current version only)."""

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_build_produces_output(self, mock_run_cmd, git_repo_path):
        """Run full no-diff workflow and verify output files."""
        output_dir = git_repo_path / "output"

        # Simulate PDF creation during compilation
        def fake_compile(cmd, cwd, timeout=300):
            if cmd[0] in ("xelatex", "pdflatex", "lualatex"):
                pdf_path = Path(cwd) / "main.pdf"
                pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_run_cmd.side_effect = fake_compile

        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            compiler="xelatex",
            output_dir=output_dir,
            build_dir=git_repo_path / "build",
            no_diff=True,
            quiet=True,
        )

        tool = LatexDiffTool(config)
        result = tool.run()

        assert result == 0
        # Should have produced a PDF
        pdf_files = list(output_dir.glob("*.pdf"))
        assert len(pdf_files) == 1

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_revision_file_generated(self, mock_run_cmd, git_repo_path):
        """Verify revision.tex is created during build."""
        def fake_compile(cmd, cwd, timeout=300):
            if cmd[0] in ("xelatex", "pdflatex", "lualatex"):
                pdf_path = Path(cwd) / "main.pdf"
                pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_run_cmd.side_effect = fake_compile

        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            output_dir=git_repo_path / "output",
            build_dir=git_repo_path / "build",
            no_diff=True,
            quiet=True,
        )

        tool = LatexDiffTool(config)
        tool.run()

        revision_file = git_repo_path / "variables" / "revision.tex"
        assert revision_file.exists()
        content = revision_file.read_text()
        assert "\\newcommand" in content


class TestFullWorkflowDiffOnly:
    """Test diff-only mode (generate diff tex without building PDFs)."""

    @patch("latex_builder.latex.processor.subprocess.run")
    def test_diff_only_produces_tex_file(self, mock_subprocess, git_repo_path):
        """Run diff-only and verify .tex diff is generated."""
        output_dir = git_repo_path / "output"

        # Mock latexdiff output
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="\\documentclass{article}\\begin{document}DIFF\\end{document}",
        )

        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            output_dir=output_dir,
            build_dir=git_repo_path / "build",
            diff_only=True,
            quiet=True,
        )

        tool = LatexDiffTool(config)
        result = tool.run()

        assert result == 0
        tex_files = list(output_dir.glob("*-vs-*.tex"))
        assert len(tex_files) == 1
        assert "vs" in tex_files[0].name


class TestFullWorkflowWithDiff:
    """Test full workflow with build + diff."""

    @patch("latex_builder.latex.processor.subprocess.run")
    @patch("latex_builder.latex.processor.run_latex_command")
    def test_full_workflow_produces_all_outputs(
        self, mock_run_cmd, mock_subprocess, git_repo_path
    ):
        """Full workflow should produce: current PDF, diff PDF, metadata.json."""
        output_dir = git_repo_path / "output"

        def fake_compile(cmd, cwd, timeout=300):
            if cmd[0] in ("xelatex", "pdflatex", "lualatex"):
                # Find the .tex file being compiled
                tex_file = cmd[-1]
                basename = Path(tex_file).stem
                pdf_path = Path(cwd) / f"{basename}.pdf"
                pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_run_cmd.side_effect = fake_compile

        # Mock latexdiff
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="\\documentclass{article}\\begin{document}DIFF\\end{document}",
        )

        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            output_dir=output_dir,
            build_dir=git_repo_path / "build",
            quiet=True,
        )

        tool = LatexDiffTool(config)
        result = tool.run()

        assert result == 0

        # Check for metadata
        metadata_file = output_dir / "metadata.json"
        assert metadata_file.exists()

        with open(metadata_file) as f:
            metadata = json.load(f)
        assert "revisions" in metadata
        assert "current" in metadata["revisions"]
        assert "compare" in metadata["revisions"]


class TestRevisionSubcommand:
    """Test the 'revision' subcommand end-to-end."""

    def test_revision_subcommand_generates_file(self, git_repo_path):
        """Test that revision subcommand generates revision.tex."""
        output_path = git_repo_path / "variables" / "revision.tex"

        with patch("sys.argv", [
            "latex-builder", "revision", str(git_repo_path),
            "--revision-file", str(output_path),
            "-q",
        ]):
            result = main()

        assert result == 0
        assert output_path.exists()
        content = output_path.read_text()
        assert "\\newcommand{\\GitCommit}" in content


class TestErrorHandling:
    """Test error handling in the full workflow."""

    def test_missing_tex_file(self, git_repo_path):
        """Should return 1 when the tex file doesn't exist."""
        config = Config(
            repo_path=git_repo_path,
            tex_file="nonexistent.tex",
            quiet=True,
        )
        tool = LatexDiffTool(config)
        assert tool.run() == 1

    def test_invalid_repo_path(self, tmp_path):
        """Should raise ValueError for non-git directory."""
        with pytest.raises(ValueError, match="Error initializing Git repository"):
            config = Config(repo_path=tmp_path / "not-a-repo")
            LatexDiffTool(config)

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_build_failure_returns_1(self, mock_run_cmd, git_repo_path):
        """Build failures should propagate and return exit code 1."""
        mock_run_cmd.side_effect = RuntimeError("Compilation failed")

        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            output_dir=git_repo_path / "output",
            no_diff=True,
            quiet=True,
        )

        tool = LatexDiffTool(config)
        assert tool.run() == 1


class TestCompareWithFlag:
    """Test the --compare-with option."""

    @patch("latex_builder.latex.processor.subprocess.run")
    @patch("latex_builder.latex.processor.run_latex_command")
    def test_compare_with_specific_tag(
        self, mock_run_cmd, mock_subprocess, git_repo_path
    ):
        """Test comparing with a specific tag."""
        output_dir = git_repo_path / "output"

        def fake_compile(cmd, cwd, timeout=300):
            if cmd[0] in ("xelatex", "pdflatex", "lualatex"):
                tex_file = cmd[-1]
                basename = Path(tex_file).stem
                pdf_path = Path(cwd) / f"{basename}.pdf"
                pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_run_cmd.side_effect = fake_compile
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="diff content",
        )

        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            output_dir=output_dir,
            build_dir=git_repo_path / "build",
            compare_with="v0.1.0",
            quiet=True,
        )

        tool = LatexDiffTool(config)
        result = tool.run()
        assert result == 0

    def test_compare_with_nonexistent_tag(self, git_repo_path):
        """Should return 1 when compare target doesn't exist."""
        config = Config(
            repo_path=git_repo_path,
            tex_file="main.tex",
            compare_with="v99.99.99",
            quiet=True,
        )
        tool = LatexDiffTool(config)
        assert tool.run() == 1
