"""Tests for latex_builder.config."""

from pathlib import Path

from latex_builder.config import Compiler, Config, SUPPORTED_COMPILERS


class TestDefaults:
    def test_default_values(self):
        c = Config()
        assert c.tex_file == "main.tex"
        assert c.compiler == Compiler.XELATEX
        assert c.compare_with is None
        assert c.timeout == 300
        assert c.skip_diff is False
        assert c.diff_only is False

    def test_immutable(self):
        c = Config()
        try:
            c.tex_file = "other.tex"  # type: ignore[misc]
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestCompilerEnum:
    def test_values(self):
        assert Compiler.XELATEX.value == "xelatex"
        assert Compiler.PDFLATEX.value == "pdflatex"
        assert Compiler.LUALATEX.value == "lualatex"

    def test_supported_list_matches(self):
        assert set(SUPPORTED_COMPILERS) == {c.value for c in Compiler}

    def test_string_conversion(self):
        assert Compiler("xelatex") is Compiler.XELATEX
