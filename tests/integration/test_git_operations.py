"""Integration tests for GitRepository with real Git repositories.

These tests use actual Git repositories created via the fixtures in conftest.py.
"""

import subprocess
from pathlib import Path

import pytest

from latex_builder.git.repository import GitRepository


class TestGetCurrentRevision:
    """Test get_current_revision with real repos."""

    def test_returns_revision_with_commit_hash(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        assert revision.commit_hash is not None
        assert len(revision.commit_hash) == 40

    def test_branch_name_is_set(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        # Default branch could be main or master
        assert revision.branch_name is not None

    def test_author_info_populated(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        assert revision.author_name == "Test User"
        assert revision.author_email == "test@example.com"

    def test_commit_summary(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        assert revision.commit_summary == "Second commit with changes"

    def test_version_name_generated(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        assert revision.version_name is not None
        assert len(revision.version_name) > 0

    def test_timestamp_is_set(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        assert revision.timestamp is not None


class TestGetPreviousCommit:
    """Test get_previous_commit with real repos."""

    def test_returns_parent_commit(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        prev = repo.get_previous_commit()
        assert prev is not None
        assert prev.commit_summary == "First commit"

    def test_single_commit_returns_none(self, git_repo_single_commit):
        repo = GitRepository(git_repo_single_commit)
        prev = repo.get_previous_commit()
        assert prev is None

    def test_parent_has_version_name(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        prev = repo.get_previous_commit()
        assert prev.version_name is not None


class TestGetPreviousTag:
    """Test get_previous_tag with real repos."""

    def test_finds_previous_tag(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        tag_rev = repo.get_previous_tag()
        assert tag_rev is not None
        assert tag_rev.tag_name == "v0.1.0"

    def test_no_tags_returns_none_or_parent(self, git_repo_no_tags):
        repo = GitRepository(git_repo_no_tags)
        result = repo.get_previous_tag()
        # With no tags, should fall back to parent commit or return None
        # Based on the code, it returns None when no tags exist
        assert result is None

    def test_multiple_tags_returns_a_previous_tag(self, git_repo_multiple_tags):
        repo = GitRepository(git_repo_multiple_tags)
        tag_rev = repo.get_previous_tag()
        assert tag_rev is not None
        # Should return one of the tags (not pointing to current commit)
        assert tag_rev.tag_name in ("v0.1.0", "v0.2.0", "v1.0.0")


class TestGetRevisionByRef:
    """Test get_revision_by_ref with real repos."""

    def test_lookup_by_tag_name(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        rev = repo.get_revision_by_ref("v0.1.0")
        assert rev is not None
        assert rev.tag_name == "v0.1.0"

    def test_lookup_by_commit_hash(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        current = repo.get_current_revision()
        rev = repo.get_revision_by_ref(current.commit_hash)
        assert rev is not None
        assert rev.commit_hash == current.commit_hash

    def test_lookup_by_short_hash(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        current = repo.get_current_revision()
        rev = repo.get_revision_by_ref(current.short_hash)
        assert rev is not None

    def test_nonexistent_ref_returns_none(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        rev = repo.get_revision_by_ref("nonexistent-ref-xyz")
        assert rev is None


class TestIsWorkingTreeDirty:
    """Test is_working_tree_dirty with real repos."""

    def test_clean_repo(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        assert repo.is_working_tree_dirty() is False

    def test_dirty_repo(self, git_repo_path):
        # Modify a tracked file to make the repo dirty
        (git_repo_path / "main.tex").write_text("modified content")
        repo = GitRepository(git_repo_path)
        assert repo.is_working_tree_dirty() is True


class TestGetLatestSemverTag:
    """Test get_latest_semver_tag with real repos."""

    def test_single_tag(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        tag = repo.get_latest_semver_tag()
        assert tag == "v0.1.0"

    def test_multiple_tags(self, git_repo_multiple_tags):
        repo = GitRepository(git_repo_multiple_tags)
        tag = repo.get_latest_semver_tag()
        assert tag == "v1.0.0"

    def test_no_tags(self, git_repo_no_tags):
        repo = GitRepository(git_repo_no_tags)
        tag = repo.get_latest_semver_tag()
        assert tag is None


class TestGenerateRevisionFile:
    """Test generate_revision_file with real repos."""

    def test_creates_revision_tex(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        output_path = tmp_path / "variables" / "revision.tex"

        repo.generate_revision_file(revision, output_path)

        assert output_path.exists()

    def test_revision_tex_contains_commands(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        output_path = tmp_path / "revision.tex"

        repo.generate_revision_file(revision, output_path)

        content = output_path.read_text()
        assert "\\newcommand{\\GitCommit}" in content
        assert "\\newcommand{\\GitTag}" in content
        assert "\\newcommand{\\GitBranch}" in content
        assert "\\newcommand{\\GitRevision}" in content
        assert "\\newcommand{\\CompiledDate}" in content

    def test_revision_tex_commit_hash(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        output_path = tmp_path / "revision.tex"

        repo.generate_revision_file(revision, output_path)

        content = output_path.read_text()
        assert revision.short_hash in content

    def test_creates_parent_directory(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        output_path = tmp_path / "deep" / "nested" / "dir" / "revision.tex"

        repo.generate_revision_file(revision, output_path)

        assert output_path.exists()


class TestCheckoutRevision:
    """Test checkout_revision with real repos."""

    def test_checks_out_revision(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        target_dir = tmp_path / "checkout"

        repo.checkout_revision(revision, target_dir)

        assert target_dir.exists()
        assert (target_dir / ".git").exists()
        assert (target_dir / "main.tex").exists()

    def test_checkout_by_string_hash(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        current = repo.get_current_revision()
        target_dir = tmp_path / "checkout"

        repo.checkout_revision(current.commit_hash, target_dir)

        assert (target_dir / "main.tex").exists()

    def test_checkout_older_revision(self, git_repo_path, tmp_path):
        repo = GitRepository(git_repo_path)
        prev = repo.get_previous_commit()
        assert prev is not None

        target_dir = tmp_path / "old_checkout"
        repo.checkout_revision(prev, target_dir)

        content = (target_dir / "main.tex").read_text()
        assert "v1" in content
        assert "v2" not in content


class TestVersionNaming:
    """Test version naming with real repos."""

    def test_untagged_commit_has_snapshot(self, git_repo_path):
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        # Current commit is not tagged, so it should contain "snapshot"
        assert "snapshot" in revision.version_name

    def test_tagged_commit_no_snapshot(self, git_repo_multiple_tags):
        repo = GitRepository(git_repo_multiple_tags)
        # Look up the tagged commit
        rev = repo.get_revision_by_ref("v1.0.0")
        assert rev is not None
        assert "snapshot" not in rev.version_name

    def test_dirty_suffix(self, git_repo_path):
        # Modify a tracked file to make the repo dirty
        (git_repo_path / "main.tex").write_text("dirty content")
        repo = GitRepository(git_repo_path)
        revision = repo.get_current_revision()
        assert "dirty" in revision.version_name
