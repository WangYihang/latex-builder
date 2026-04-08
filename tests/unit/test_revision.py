"""Unit tests for latex_builder.git.revision.GitRevision."""

import datetime
from datetime import timezone

from latex_builder.git.revision import GitRevision


class TestShortHash:
    """Test GitRevision.short_hash property."""

    def test_returns_first_7_chars(self):
        rev = GitRevision(commit_hash="abcdef1234567890")
        assert rev.short_hash == "abcdef1"

    def test_exact_7_char_hash(self):
        rev = GitRevision(commit_hash="1234567")
        assert rev.short_hash == "1234567"

    def test_full_40_char_hash(self):
        rev = GitRevision(commit_hash="a" * 40)
        assert rev.short_hash == "aaaaaaa"


class TestDisplayName:
    """Test GitRevision.display_name property."""

    def test_version_name_takes_priority(self):
        rev = GitRevision(
            commit_hash="abcdef1234567890",
            tag_name="v1.0.0",
            version_name="v1.0.0-abcdef1-20240101",
        )
        assert rev.display_name == "v1.0.0-abcdef1-20240101"

    def test_tag_name_with_short_hash(self):
        rev = GitRevision(
            commit_hash="abcdef1234567890",
            tag_name="v1.0.0",
        )
        assert rev.display_name == "v1.0.0-abcdef1"

    def test_ref_name_with_short_hash(self):
        rev = GitRevision(
            commit_hash="abcdef1234567890",
            ref_name="main",
        )
        assert rev.display_name == "main-abcdef1"

    def test_branch_name_appended_when_different(self):
        rev = GitRevision(
            commit_hash="abcdef1234567890",
            ref_name="feature",
            branch_name="develop",
        )
        assert rev.display_name == "feature-develop-abcdef1"

    def test_branch_name_not_duplicated(self):
        rev = GitRevision(
            commit_hash="abcdef1234567890",
            tag_name="v1.0.0",
            branch_name="v1.0.0",
        )
        assert rev.display_name == "v1.0.0-abcdef1"

    def test_only_hash_as_fallback(self):
        rev = GitRevision(commit_hash="abcdef1234567890")
        assert rev.display_name == "abcdef1"

    def test_branch_name_alone_with_hash(self):
        rev = GitRevision(
            commit_hash="abcdef1234567890",
            branch_name="feature-branch",
        )
        assert rev.display_name == "feature-branch-abcdef1"


class TestGitRevisionDataclass:
    """Test GitRevision dataclass fields and defaults."""

    def test_only_commit_hash_required(self):
        rev = GitRevision(commit_hash="abc123")
        assert rev.commit_hash == "abc123"
        assert rev.tag_name is None
        assert rev.branch_name is None
        assert rev.ref_name is None
        assert rev.is_dirty is False
        assert rev.version_name is None
        assert rev.timestamp is None
        assert rev.author_name is None
        assert rev.author_email is None
        assert rev.commit_summary is None
        assert rev.commit_message is None
        assert rev.commit_date_iso is None  # derived from timestamp

    def test_all_fields_populated(self, sample_revision):
        rev = sample_revision
        assert rev.commit_hash == "abcdef1234567890abcdef1234567890abcdef12"
        assert rev.tag_name == "v1.0.0"
        assert rev.branch_name == "main"
        assert rev.author_name == "Test Author"
        assert rev.author_email == "test@example.com"
        assert rev.commit_summary == "Initial commit"
        assert rev.is_dirty is False

    def test_dirty_flag(self):
        rev = GitRevision(commit_hash="abc123", is_dirty=True)
        assert rev.is_dirty is True

    def test_timestamp_field(self):
        ts = datetime.datetime(2024, 1, 1, tzinfo=timezone.utc)
        rev = GitRevision(commit_hash="abc123", timestamp=ts)
        assert rev.timestamp == ts
