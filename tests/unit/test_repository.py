"""Unit tests for latex_builder.git.repository.GitRepository.

These tests focus on pure logic methods (semver parsing, version naming)
that can be tested without a real Git repository.
For tests requiring a real repo, see tests/integration/test_git_operations.py.
"""

import datetime
from datetime import timezone
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from latex_builder.git.repository import GitRepository
from latex_builder.git.revision import GitRevision


# ---------------------------------------------------------------------------
# Helper: create a GitRepository with mocked git.Repo
# ---------------------------------------------------------------------------

def _make_repo_with_mock(tags=None):
    """Create a GitRepository with a mocked internal git.Repo."""
    with patch("latex_builder.git.repository.git.Repo") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.head.is_detached = False
        mock_repo.active_branch.name = "main"

        if tags is not None:
            mock_tags = []
            for name in tags:
                tag = MagicMock()
                tag.name = name
                mock_tags.append(tag)
            mock_repo.tags = mock_tags
        else:
            mock_repo.tags = []

        repo = GitRepository()
        return repo


class TestParseSemver:
    """Test GitRepository.parse_semver method."""

    def test_valid_version_with_v_prefix(self):
        repo = _make_repo_with_mock()
        result = repo.parse_semver("v1.2.3")
        assert result is not None
        assert result.major == 1
        assert result.minor == 2
        assert result.patch == 3

    def test_valid_version_without_prefix(self):
        repo = _make_repo_with_mock()
        result = repo.parse_semver("1.2.3")
        assert result is not None
        assert result.major == 1

    def test_invalid_version_returns_none(self):
        repo = _make_repo_with_mock()
        assert repo.parse_semver("not-a-version") is None

    def test_partial_version_returns_none(self):
        repo = _make_repo_with_mock()
        assert repo.parse_semver("v1.2") is None

    def test_zero_version(self):
        repo = _make_repo_with_mock()
        result = repo.parse_semver("v0.0.0")
        assert result is not None
        assert result.major == 0

    def test_large_version_numbers(self):
        repo = _make_repo_with_mock()
        result = repo.parse_semver("v100.200.300")
        assert result is not None
        assert result.patch == 300


class TestBumpPatch:
    """Test GitRepository.bump_patch method."""

    def test_bumps_patch_version(self):
        repo = _make_repo_with_mock()
        assert repo.bump_patch("v1.2.3") == "v1.2.4"

    def test_bumps_from_zero(self):
        repo = _make_repo_with_mock()
        assert repo.bump_patch("v0.0.0") == "v0.0.1"

    def test_invalid_version_returns_fallback(self):
        repo = _make_repo_with_mock()
        assert repo.bump_patch("not-a-version") == "v0.0.1"

    def test_without_v_prefix(self):
        repo = _make_repo_with_mock()
        assert repo.bump_patch("1.0.0") == "v1.0.1"


class TestGetLatestSemverTag:
    """Test GitRepository.get_latest_semver_tag method."""

    def test_returns_highest_tag(self):
        repo = _make_repo_with_mock(tags=["v0.1.0", "v1.0.0", "v0.2.0"])
        result = repo.get_latest_semver_tag()
        assert result == "v1.0.0"

    def test_no_tags_returns_none(self):
        repo = _make_repo_with_mock(tags=[])
        assert repo.get_latest_semver_tag() is None

    def test_filters_non_semver_tags(self):
        repo = _make_repo_with_mock(tags=["release-1", "v0.1.0", "latest"])
        result = repo.get_latest_semver_tag()
        assert result == "v0.1.0"

    def test_all_non_semver_returns_none(self):
        repo = _make_repo_with_mock(tags=["release-1", "latest", "beta"])
        assert repo.get_latest_semver_tag() is None


class TestGenerateVersionName:
    """Test GitRepository.generate_version_name method."""

    def test_tagged_commit(self):
        repo = _make_repo_with_mock(tags=["v1.0.0"])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            tag_name="v1.0.0",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        name = repo.generate_version_name(revision)
        assert name.startswith("v1.0.0-abcdef1-")
        assert "snapshot" not in name

    def test_untagged_commit_with_latest_tag(self):
        repo = _make_repo_with_mock(tags=["v1.0.0"])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        name = repo.generate_version_name(revision)
        assert "v1.0.1" in name
        assert "snapshot" in name
        assert "abcdef1" in name

    def test_untagged_commit_no_tags(self):
        repo = _make_repo_with_mock(tags=[])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        name = repo.generate_version_name(revision)
        assert "v0.0.1" in name
        assert "snapshot" in name

    def test_dirty_flag_appended(self):
        repo = _make_repo_with_mock(tags=[])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            is_dirty=True,
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        name = repo.generate_version_name(revision)
        assert "dirty" in name

    def test_clean_no_dirty_suffix(self):
        repo = _make_repo_with_mock(tags=[])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            is_dirty=False,
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        )
        name = repo.generate_version_name(revision)
        assert "dirty" not in name

    def test_timestamp_format(self):
        repo = _make_repo_with_mock(tags=[])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            timestamp=datetime.datetime(2024, 3, 15, 9, 30, 45, tzinfo=timezone.utc),
        )
        name = repo.generate_version_name(revision)
        assert "20240315093045" in name

    def test_no_timestamp(self):
        repo = _make_repo_with_mock(tags=[])
        revision = GitRevision(
            commit_hash="abcdef1234567890",
            timestamp=None,
        )
        name = repo.generate_version_name(revision)
        # Should still work without timestamp
        assert "abcdef1" in name


class TestInitInvalidPath:
    """Test GitRepository initialization with invalid path."""

    def test_invalid_path_raises_value_error(self, tmp_path):
        with pytest.raises(ValueError, match="Error initializing Git repository"):
            GitRepository(tmp_path / "nonexistent")
