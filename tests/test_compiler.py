"""Tests for latex_builder.compiler."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from latex_builder.compiler import build, latexdiff
from latex_builder.config import Compiler


class TestBuild:
    @patch("latex_builder.compiler.shell.run_latex")
    def test_copies_pdf(self, mock_run, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        out = tmp_path / "out"

        def create_pdf(*a, **kw):
            (work / "main.pdf").write_bytes(b"%PDF")

        mock_run.side_effect = create_pdf

        result = build("main.tex", working_dir=work, output_dir=out, output_name="result.pdf")
        assert result == out / "result.pdf"
        assert result.read_bytes() == b"%PDF"

    @patch("latex_builder.compiler.shell.run_latex")
    def test_raises_if_no_pdf(self, mock_run, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        with pytest.raises(RuntimeError, match="PDF not produced"):
            build("main.tex", working_dir=work, output_dir=tmp_path / "out")

    @patch("latex_builder.compiler.shell.run_latex")
    def test_four_commands(self, mock_run, tmp_path):
        """compiler → bibtex → compiler → compiler = 4 calls."""
        work = tmp_path / "work"
        work.mkdir()

        def create_pdf(*a, **kw):
            (work / "main.pdf").write_bytes(b"%PDF")

        mock_run.side_effect = create_pdf

        build("main.tex", working_dir=work, output_dir=tmp_path / "out")
        assert mock_run.call_count == 4

    @patch("latex_builder.compiler.shell.run_latex")
    def test_bibtex_failure_tolerated(self, mock_run, tmp_path):
        work = tmp_path / "work"
        work.mkdir()
        call_count = [0]

        def side_effect(cmd, **kw):
            call_count[0] += 1
            if cmd[0] == "bibtex":
                raise RuntimeError("no .bib")
            (work / "main.pdf").write_bytes(b"%PDF")

        mock_run.side_effect = side_effect

        build("main.tex", working_dir=work, output_dir=tmp_path / "out")
        assert call_count[0] == 4

    @patch("latex_builder.compiler.shell.run_latex")
    def test_pdflatex(self, mock_run, tmp_path):
        work = tmp_path / "work"
        work.mkdir()

        def create_pdf(*a, **kw):
            (work / "main.pdf").write_bytes(b"%PDF")

        mock_run.side_effect = create_pdf

        build("main.tex", working_dir=work, output_dir=tmp_path / "out", compiler=Compiler.PDFLATEX)
        first_call = mock_run.call_args_list[0].args[0]
        assert first_call[0] == "pdflatex"


class TestLatexdiff:
    @patch("latex_builder.compiler.subprocess.run")
    def test_writes_output(self, mock_run, tmp_path):
        old = tmp_path / "old.tex"
        new = tmp_path / "new.tex"
        out = tmp_path / "diff.tex"
        old.write_text("old")
        new.write_text("new")

        mock_run.return_value = MagicMock(returncode=0, stdout="diff content")
        latexdiff(old, new, out)
        assert out.read_text() == "diff content"

    @patch("latex_builder.compiler.subprocess.run")
    def test_uses_flatten(self, mock_run, tmp_path):
        old = tmp_path / "a.tex"
        new = tmp_path / "b.tex"
        old.write_text("a")
        new.write_text("b")
        mock_run.return_value = MagicMock(returncode=0, stdout="x")

        latexdiff(old, new, tmp_path / "d.tex")
        assert "--flatten" in mock_run.call_args.args[0]
