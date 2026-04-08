"""Unit tests for latex_builder.latex.processor.LaTeXProcessor."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from latex_builder.latex.processor import LaTeXProcessor


class TestLaTeXProcessorInit:
    """Test LaTeXProcessor initialization."""

    def test_default_base_dir_is_cwd(self):
        processor = LaTeXProcessor()
        assert processor.base_dir == Path.cwd()

    def test_custom_base_dir(self, tmp_path):
        processor = LaTeXProcessor(tmp_path)
        assert processor.base_dir == tmp_path


class TestBuildDocument:
    """Test LaTeXProcessor.build_document method."""

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_successful_build_copies_pdf(self, mock_run, tmp_path):
        # Setup: create a fake PDF that the "compilation" produces
        working_dir = tmp_path / "work"
        working_dir.mkdir()
        output_dir = tmp_path / "output"

        processor = LaTeXProcessor(working_dir)

        # Simulate: after run_latex_command, a PDF appears
        def create_pdf(*args, **kwargs):
            (working_dir / "main.pdf").write_bytes(b"%PDF-fake")

        mock_run.side_effect = create_pdf

        processor.build_document(
            "main.tex", working_dir, output_dir, "result.pdf", "xelatex"
        )

        assert (output_dir / "result.pdf").exists()
        assert (output_dir / "result.pdf").read_bytes() == b"%PDF-fake"

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_raises_when_pdf_not_found(self, mock_run, tmp_path):
        working_dir = tmp_path / "work"
        working_dir.mkdir()

        processor = LaTeXProcessor(working_dir)

        with pytest.raises(RuntimeError, match="PDF file not found"):
            processor.build_document(
                "main.tex", working_dir, tmp_path / "output", "result.pdf", "xelatex"
            )

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_creates_output_directory(self, mock_run, tmp_path):
        working_dir = tmp_path / "work"
        working_dir.mkdir()
        output_dir = tmp_path / "new_output"

        processor = LaTeXProcessor(working_dir)

        def create_pdf(*args, **kwargs):
            (working_dir / "main.pdf").write_bytes(b"%PDF-fake")

        mock_run.side_effect = create_pdf

        processor.build_document(
            "main.tex", working_dir, output_dir, "result.pdf", "xelatex"
        )

        assert output_dir.exists()


class TestRunLatexCommands:
    """Test LaTeXProcessor._run_latex_commands sequence."""

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_compile_sequence_order(self, mock_run, tmp_path):
        processor = LaTeXProcessor(tmp_path)
        processor._run_latex_commands("main.tex", tmp_path, "xelatex")

        assert mock_run.call_count == 4
        calls = mock_run.call_args_list

        # First pass
        assert calls[0][0][0] == ["xelatex", "-shell-escape", "main.tex"]
        # Bibtex
        assert calls[1][0][0] == ["bibtex", "main"]
        # Second pass
        assert calls[2][0][0] == ["xelatex", "-shell-escape", "main.tex"]
        # Final pass
        assert calls[3][0][0] == ["xelatex", "-shell-escape", "main.tex"]

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_compile_with_pdflatex(self, mock_run, tmp_path):
        processor = LaTeXProcessor(tmp_path)
        processor._run_latex_commands("doc.tex", tmp_path, "pdflatex")

        calls = mock_run.call_args_list
        assert calls[0][0][0][0] == "pdflatex"
        assert calls[2][0][0][0] == "pdflatex"
        assert calls[3][0][0][0] == "pdflatex"

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_invalid_compiler_raises(self, mock_run, tmp_path):
        processor = LaTeXProcessor(tmp_path)
        with pytest.raises(RuntimeError, match="Unsupported compiler"):
            processor._run_latex_commands("main.tex", tmp_path, "latexmk")

    @patch("latex_builder.latex.processor.run_latex_command")
    def test_bibtex_uses_basename_without_extension(self, mock_run, tmp_path):
        processor = LaTeXProcessor(tmp_path)
        processor._run_latex_commands("thesis.tex", tmp_path, "xelatex")

        bibtex_call = mock_run.call_args_list[1]
        assert bibtex_call[0][0] == ["bibtex", "thesis"]


class TestGenerateDiff:
    """Test LaTeXProcessor.generate_diff method."""

    @patch("latex_builder.latex.processor.subprocess.run")
    def test_successful_diff(self, mock_run, tmp_path):
        original = tmp_path / "old.tex"
        modified = tmp_path / "new.tex"
        output = tmp_path / "diff.tex"
        original.write_text("old content")
        modified.write_text("new content")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="\\DIFaddbegin new content \\DIFaddend",
        )

        processor = LaTeXProcessor(tmp_path)
        processor.generate_diff(original, modified, output)

        assert output.exists()
        assert "DIFaddbegin" in output.read_text()

    @patch("latex_builder.latex.processor.subprocess.run")
    def test_diff_creates_output_directory(self, mock_run, tmp_path):
        original = tmp_path / "old.tex"
        modified = tmp_path / "new.tex"
        output = tmp_path / "subdir" / "diff.tex"
        original.write_text("old")
        modified.write_text("new")

        mock_run.return_value = MagicMock(returncode=0, stdout="diff output")

        processor = LaTeXProcessor(tmp_path)
        processor.generate_diff(original, modified, output)

        assert output.parent.exists()

    @patch("latex_builder.latex.processor.subprocess.run")
    def test_diff_uses_flatten_option(self, mock_run, tmp_path):
        original = tmp_path / "old.tex"
        modified = tmp_path / "new.tex"
        output = tmp_path / "diff.tex"
        original.write_text("old")
        modified.write_text("new")

        mock_run.return_value = MagicMock(returncode=0, stdout="diff")

        processor = LaTeXProcessor(tmp_path)
        processor.generate_diff(original, modified, output)

        called_cmd = mock_run.call_args[0][0]
        assert "--flatten" in called_cmd

    @patch("latex_builder.latex.processor.subprocess.run")
    def test_diff_failure_raises(self, mock_run, tmp_path):
        original = tmp_path / "old.tex"
        modified = tmp_path / "new.tex"
        output = tmp_path / "diff.tex"
        original.write_text("old")
        modified.write_text("new")

        mock_run.side_effect = Exception("latexdiff not found")

        processor = LaTeXProcessor(tmp_path)
        with pytest.raises(RuntimeError, match="Failed to generate diff"):
            processor.generate_diff(original, modified, output)
