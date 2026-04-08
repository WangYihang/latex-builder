"""Unit tests for latex_builder.diff.generator.DiffGenerator."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from latex_builder.config.settings import Config
from latex_builder.diff.generator import DiffGenerator
from latex_builder.git.revision import GitRevision


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_git_repo():
    repo = MagicMock()
    repo.checkout_revision = MagicMock()
    repo.generate_revision_file = MagicMock()
    return repo


@pytest.fixture
def mock_latex_processor():
    proc = MagicMock()
    proc.build_document = MagicMock()
    proc.generate_diff = MagicMock()
    return proc


@pytest.fixture
def generator(tmp_path, mock_git_repo, mock_latex_processor):
    config = Config(
        repo_path=tmp_path,
        output_dir=tmp_path / "output",
        build_dir=tmp_path / "build",
        tex_file="main.tex",
        compiler="xelatex",
        revision_file="variables/revision.tex",
    )
    return DiffGenerator(mock_git_repo, mock_latex_processor, config)


@pytest.fixture
def current_rev():
    return GitRevision(
        commit_hash="aaaa" * 10,
        version_name="v1.0.0-aaaaaaa-20240101120000",
    )


@pytest.fixture
def compare_rev():
    return GitRevision(
        commit_hash="bbbb" * 10,
        version_name="v0.9.0-bbbbbbb-20231215100000",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBuildCurrentOnly:
    """Test DiffGenerator.build_current_only method."""

    def test_builds_document(self, generator, current_rev, mock_latex_processor, mock_git_repo):
        generator.build_current_only(current_rev)

        mock_git_repo.generate_revision_file.assert_called_once()
        mock_latex_processor.build_document.assert_called_once()

    def test_creates_output_directory(self, generator, current_rev, tmp_path):
        output_dir = tmp_path / "output"
        assert not output_dir.exists()
        generator.build_current_only(current_rev)
        assert output_dir.exists()

    def test_propagates_build_error(self, generator, current_rev, mock_latex_processor):
        mock_latex_processor.build_document.side_effect = RuntimeError("Build failed")
        with pytest.raises(RuntimeError, match="Build failed"):
            generator.build_current_only(current_rev)


class TestSaveMetadata:
    """Test DiffGenerator._save_metadata method."""

    def test_creates_metadata_json(self, generator, current_rev, compare_rev, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        generator._save_metadata(current_rev, compare_rev)

        metadata_file = output_dir / "metadata.json"
        assert metadata_file.exists()

    def test_metadata_structure(self, generator, current_rev, compare_rev, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        generator._save_metadata(current_rev, compare_rev)

        with open(output_dir / "metadata.json") as f:
            metadata = json.load(f)

        assert "diff_generation" in metadata
        assert "revisions" in metadata
        assert "files" in metadata
        assert "repository" in metadata

    def test_metadata_contains_revision_info(self, generator, current_rev, compare_rev, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        generator._save_metadata(current_rev, compare_rev)

        with open(output_dir / "metadata.json") as f:
            metadata = json.load(f)

        current_meta = metadata["revisions"]["current"]
        assert current_meta["commit"]["hash"] == current_rev.commit_hash
        assert current_meta["version"]["display_name"] == current_rev.display_name

        compare_meta = metadata["revisions"]["compare"]
        assert compare_meta["commit"]["hash"] == compare_rev.commit_hash

    def test_metadata_diff_filenames(self, generator, current_rev, compare_rev, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        generator._save_metadata(current_rev, compare_rev)

        with open(output_dir / "metadata.json") as f:
            metadata = json.load(f)

        expected_tex = f"{compare_rev.display_name}-vs-{current_rev.display_name}.tex"
        expected_pdf = f"{compare_rev.display_name}-vs-{current_rev.display_name}.pdf"
        assert metadata["files"]["diff"]["tex"] == expected_tex
        assert metadata["files"]["diff"]["pdf"] == expected_pdf

    def test_metadata_settings(self, generator, current_rev, compare_rev, tmp_path):
        output_dir = tmp_path / "output"
        output_dir.mkdir(parents=True)

        generator._save_metadata(current_rev, compare_rev)

        with open(output_dir / "metadata.json") as f:
            metadata = json.load(f)

        settings = metadata["diff_generation"]["settings"]
        assert settings["tex_file"] == "main.tex"
        assert settings["compiler"] == "xelatex"


class TestGenerateDiffs:
    """Test DiffGenerator.generate_diffs method."""

    @patch.object(DiffGenerator, "_generate_and_build_diff")
    @patch.object(DiffGenerator, "_build_current_version")
    def test_calls_build_and_diff(self, mock_build, mock_diff, generator, current_rev, compare_rev, tmp_path):
        (tmp_path / "output").mkdir(parents=True, exist_ok=True)
        (tmp_path / "build").mkdir(parents=True, exist_ok=True)

        generator.generate_diffs(current_rev, compare_rev)

        mock_build.assert_called_once_with(current_rev)
        mock_diff.assert_called_once_with(current_rev, compare_rev)

    @patch.object(DiffGenerator, "_generate_and_build_diff")
    @patch.object(DiffGenerator, "_build_current_version")
    def test_creates_directories(self, mock_build, mock_diff, generator, current_rev, compare_rev, tmp_path):
        generator.generate_diffs(current_rev, compare_rev)
        assert (tmp_path / "output").exists()
        assert (tmp_path / "build").exists()

    @patch.object(DiffGenerator, "_generate_and_build_diff")
    @patch.object(DiffGenerator, "_build_current_version")
    def test_saves_metadata(self, mock_build, mock_diff, generator, current_rev, compare_rev, tmp_path):
        (tmp_path / "output").mkdir(parents=True, exist_ok=True)

        generator.generate_diffs(current_rev, compare_rev)

        assert (tmp_path / "output" / "metadata.json").exists()

    @patch.object(DiffGenerator, "_generate_and_build_diff")
    @patch.object(DiffGenerator, "_build_current_version")
    def test_build_failure_propagates(self, mock_build, mock_diff, generator, current_rev, compare_rev):
        mock_build.side_effect = RuntimeError("build failed")
        with pytest.raises(RuntimeError):
            generator.generate_diffs(current_rev, compare_rev)


class TestPrepareCheckoutDirectories:
    """Test DiffGenerator._prepare_checkout_directories method."""

    def test_returns_playground_path(self, generator, current_rev, compare_rev, mock_git_repo):
        # Make checkout_revision a no-op
        mock_git_repo.checkout_revision = MagicMock()

        # We need to patch GitRepository constructor for _run_revision_in_directory
        with patch("latex_builder.diff.generator.GitRepository") as MockRepo:
            MockRepo.return_value.generate_revision_file = MagicMock()
            result = generator._prepare_checkout_directories(current_rev, compare_rev)

        assert "playground" in result
        assert "current" in result
        assert "compare" in result
        assert result["playground"].exists()

        # Cleanup
        import shutil
        shutil.rmtree(result["playground"], ignore_errors=True)

    def test_checkout_called_for_both_revisions(self, generator, current_rev, compare_rev, mock_git_repo):
        with patch("latex_builder.diff.generator.GitRepository") as MockRepo:
            MockRepo.return_value.generate_revision_file = MagicMock()
            result = generator._prepare_checkout_directories(current_rev, compare_rev)

        assert mock_git_repo.checkout_revision.call_count == 2

        import shutil
        shutil.rmtree(result["playground"], ignore_errors=True)
