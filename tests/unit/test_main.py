"""Unit tests for latex_builder.cli.main.LatexDiffTool."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from latex_builder.cli.main import LatexDiffTool
from latex_builder.config.settings import Config
from latex_builder.git.revision import GitRevision


@pytest.fixture
def mock_revision():
    return GitRevision(
        commit_hash="a" * 40,
        version_name="v1.0.0-aaaaaaa-20240101",
    )


@pytest.fixture
def mock_compare_revision():
    return GitRevision(
        commit_hash="b" * 40,
        version_name="v0.9.0-bbbbbbb-20231215",
    )


class TestLatexDiffToolRun:
    """Test LatexDiffTool.run method."""

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_returns_1_when_tex_file_missing(self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path):
        config = Config(repo_path=tmp_path, tex_file="missing.tex")
        tool = LatexDiffTool(config)
        assert tool.run() == 1

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_returns_0_on_success_no_diff(self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision):
        # Create the tex file
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = None
        mock_repo.get_previous_commit.return_value = mock_revision

        config = Config(repo_path=tmp_path, no_diff=True)
        tool = LatexDiffTool(config)
        result = tool.run()
        assert result == 0

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_no_diff_mode_calls_build_current_only(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = mock_revision

        config = Config(repo_path=tmp_path, no_diff=True)
        tool = LatexDiffTool(config)
        tool.run()

        MockDiffGen.return_value.build_current_only.assert_called_once()

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_diff_only_mode_calls_generate_diff_only(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = mock_revision

        config = Config(repo_path=tmp_path, diff_only=True)
        tool = LatexDiffTool(config)
        tool.run()

        MockDiffGen.return_value.generate_diff_only.assert_called_once()

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_full_mode_calls_generate_diffs(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = mock_revision

        config = Config(repo_path=tmp_path)
        tool = LatexDiffTool(config)
        tool.run()

        MockDiffGen.return_value.generate_diffs.assert_called_once()

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_specified_compare_target_not_found(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_revision_by_ref.return_value = None

        config = Config(repo_path=tmp_path, compare_with="nonexistent-tag")
        tool = LatexDiffTool(config)
        assert tool.run() == 1

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_no_previous_commit_returns_1(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = None
        mock_repo.get_previous_commit.return_value = None

        config = Config(repo_path=tmp_path)
        tool = LatexDiffTool(config)
        assert tool.run() == 1

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_exception_returns_1(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.side_effect = RuntimeError("git error")

        config = Config(repo_path=tmp_path)
        tool = LatexDiffTool(config)
        assert tool.run() == 1

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_auto_selects_previous_tag(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision, mock_compare_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = mock_compare_revision

        config = Config(repo_path=tmp_path, no_diff=True)
        tool = LatexDiffTool(config)
        tool.run()

        # Should not call get_previous_commit since tag was found
        mock_repo.get_previous_commit.assert_not_called()

    @patch("latex_builder.cli.main.DiffGenerator")
    @patch("latex_builder.cli.main.LaTeXProcessor")
    @patch("latex_builder.cli.main.GitRepository")
    def test_falls_back_to_previous_commit(
        self, MockGitRepo, MockProcessor, MockDiffGen, tmp_path, mock_revision, mock_compare_revision
    ):
        (tmp_path / "main.tex").write_text("\\documentclass{article}")

        mock_repo = MockGitRepo.return_value
        mock_repo.get_current_revision.return_value = mock_revision
        mock_repo.get_previous_tag.return_value = None
        mock_repo.get_previous_commit.return_value = mock_compare_revision

        config = Config(repo_path=tmp_path, no_diff=True)
        tool = LatexDiffTool(config)
        result = tool.run()

        assert result == 0
        mock_repo.get_previous_commit.assert_called_once()
