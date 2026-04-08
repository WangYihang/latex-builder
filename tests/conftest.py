"""Shared test fixtures."""

from __future__ import annotations

import datetime
import subprocess
from datetime import timezone
from pathlib import Path

import pytest

from latex_builder.revision import Revision


# ------------------------------------------------------------------
# Revision fixtures
# ------------------------------------------------------------------

@pytest.fixture
def sample_rev() -> Revision:
    return Revision(
        commit_hash="abcdef1234567890abcdef1234567890abcdef12",
        tag="v1.0.0",
        branch="main",
        is_dirty=False,
        version_name="v1.0.0-abcdef1",
        timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        author_name="Test Author",
        author_email="test@example.com",
        summary="Initial commit",
        message="Initial commit\n\nDetails",
    )


@pytest.fixture
def compare_rev() -> Revision:
    return Revision(
        commit_hash="1234567890abcdef1234567890abcdef12345678",
        tag="v0.9.0",
        branch="main",
        version_name="v0.9.0-1234567",
        timestamp=datetime.datetime(2023, 12, 15, 10, 0, 0, tzinfo=timezone.utc),
        author_name="Other Author",
        author_email="other@example.com",
        summary="Previous release",
        message="Previous release",
    )


# ------------------------------------------------------------------
# Git repo helpers
# ------------------------------------------------------------------

def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, check=True)


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test User")
    _git(path, "config", "commit.gpgsign", "false")
    return path


def _commit(path: Path, msg: str) -> None:
    _git(path, "add", ".")
    _git(path, "commit", "-m", msg)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Repo with two commits and a v0.1.0 tag on the first."""
    repo = _init_repo(tmp_path / "repo")
    (repo / "main.tex").write_text(
        r"\documentclass{article}\begin{document}Hello v1\end{document}" + "\n"
    )
    _commit(repo, "First commit")
    _git(repo, "tag", "v0.1.0")

    (repo / "main.tex").write_text(
        r"\documentclass{article}\begin{document}Hello v2\end{document}" + "\n"
    )
    _commit(repo, "Second commit")
    return repo


@pytest.fixture
def git_repo_single(tmp_path: Path) -> Path:
    """Repo with exactly one commit (no parent)."""
    repo = _init_repo(tmp_path / "single")
    (repo / "main.tex").write_text(r"\documentclass{article}\begin{document}Hi\end{document}")
    _commit(repo, "Initial commit")
    return repo


@pytest.fixture
def git_repo_no_tags(tmp_path: Path) -> Path:
    """Repo with two commits but no tags."""
    repo = _init_repo(tmp_path / "notags")
    (repo / "main.tex").write_text("v1")
    _commit(repo, "First")
    (repo / "main.tex").write_text("v2")
    _commit(repo, "Second")
    return repo


@pytest.fixture
def git_repo_multi_tags(tmp_path: Path) -> Path:
    """Repo with v0.1.0, v0.2.0, v1.0.0 tags + one untagged HEAD."""
    repo = _init_repo(tmp_path / "multi")
    f = repo / "main.tex"
    for tag in ("v0.1.0", "v0.2.0", "v1.0.0"):
        f.write_text(f"content for {tag}")
        _commit(repo, f"Release {tag}")
        _git(repo, "tag", tag)
    f.write_text("post-release")
    _commit(repo, "Post-release")
    return repo
