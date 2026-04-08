"""Shared test fixtures for latex-builder test suite."""

import datetime
import shutil
import subprocess
import tempfile
from datetime import timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from latex_builder.config.settings import Config
from latex_builder.git.revision import GitRevision


# ---------------------------------------------------------------------------
# GitRevision fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_revision():
    """A typical GitRevision with all fields populated."""
    return GitRevision(
        commit_hash="abcdef1234567890abcdef1234567890abcdef12",
        tag_name="v1.0.0",
        branch_name="main",
        ref_name=None,
        is_dirty=False,
        version_name="v1.0.0-abcdef1-20240101120000",
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        author_name="Test Author",
        author_email="test@example.com",
        commit_summary="Initial commit",
        commit_message="Initial commit\n\nDetailed description",
        commit_date=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        commit_date_iso="2024-01-01T12:00:00+00:00",
    )


@pytest.fixture
def compare_revision():
    """A second GitRevision for comparison tests."""
    return GitRevision(
        commit_hash="1234567890abcdef1234567890abcdef12345678",
        tag_name="v0.9.0",
        branch_name="main",
        ref_name=None,
        is_dirty=False,
        version_name="v0.9.0-1234567-20231215100000",
        timestamp=datetime.datetime(2023, 12, 15, 10, 0, 0, tzinfo=timezone.utc),
        author_name="Other Author",
        author_email="other@example.com",
        commit_summary="Previous release",
        commit_message="Previous release",
        commit_date=datetime.datetime(2023, 12, 15, 10, 0, 0, tzinfo=timezone.utc),
        commit_date_iso="2023-12-15T10:00:00+00:00",
    )


@pytest.fixture
def minimal_revision():
    """A GitRevision with only the required field."""
    return GitRevision(commit_hash="abcdef1234567890abcdef1234567890abcdef12")


# ---------------------------------------------------------------------------
# Config fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def default_config(tmp_path):
    """Config with default values, using tmp_path for file paths."""
    return Config(
        repo_path=tmp_path,
        output_dir=tmp_path / "output",
        build_dir=tmp_path / "build",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_init(repo_dir: Path):
    """Initialize a Git repo with test config and signing disabled."""
    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=repo_dir, capture_output=True, check=True,
    )


def _git_commit(repo_dir: Path, message: str):
    """Create a commit with signing disabled."""
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_dir, capture_output=True, check=True,
    )


# ---------------------------------------------------------------------------
# Temporary Git repository fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def git_repo_path(tmp_path):
    """Create a temporary Git repository with two commits and a tag."""
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()

    _git_init(repo_dir)

    # First commit
    tex_file = repo_dir / "main.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Hello World v1
\end{document}
"""
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    _git_commit(repo_dir, "First commit")

    # Tag first commit
    subprocess.run(
        ["git", "tag", "v0.1.0"],
        cwd=repo_dir, capture_output=True, check=True,
    )

    # Second commit
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Hello World v2 with changes
\end{document}
"""
    )
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    _git_commit(repo_dir, "Second commit with changes")

    return repo_dir


@pytest.fixture
def git_repo_single_commit(tmp_path):
    """Create a temporary Git repository with only one commit (no parent)."""
    repo_dir = tmp_path / "single-commit-repo"
    repo_dir.mkdir()

    _git_init(repo_dir)

    tex_file = repo_dir / "main.tex"
    tex_file.write_text(r"\documentclass{article}\begin{document}Hello\end{document}")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    _git_commit(repo_dir, "Initial commit")

    return repo_dir


@pytest.fixture
def git_repo_no_tags(tmp_path):
    """Create a temporary Git repository with multiple commits but no tags."""
    repo_dir = tmp_path / "no-tags-repo"
    repo_dir.mkdir()

    _git_init(repo_dir)

    tex_file = repo_dir / "main.tex"
    tex_file.write_text("v1")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    _git_commit(repo_dir, "First commit")

    tex_file.write_text("v2")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    _git_commit(repo_dir, "Second commit")

    return repo_dir


@pytest.fixture
def git_repo_multiple_tags(tmp_path):
    """Create a repo with multiple semver tags."""
    repo_dir = tmp_path / "multi-tag-repo"
    repo_dir.mkdir()

    _git_init(repo_dir)

    f = repo_dir / "main.tex"
    for i, tag in enumerate(["v0.1.0", "v0.2.0", "v1.0.0"]):
        f.write_text(f"version {i}")
        subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
        _git_commit(repo_dir, f"Release {tag}")
        subprocess.run(
            ["git", "tag", tag], cwd=repo_dir, capture_output=True, check=True,
        )

    # One more commit after the last tag
    f.write_text("post-release work")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=True)
    _git_commit(repo_dir, "Post-release work")

    return repo_dir
