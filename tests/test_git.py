"""Tests for latex_builder.git — unit tests (mocked) and integration tests (real repos)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from latex_builder.git import GitRepo, _parse_semver
from latex_builder.revision import Revision


# =====================================================================
# Unit tests (no real repo needed)
# =====================================================================

class TestParseSemver:
    def test_with_v_prefix(self):
        assert _parse_semver("v1.2.3") is not None

    def test_without_prefix(self):
        assert _parse_semver("1.2.3") is not None

    def test_invalid(self):
        assert _parse_semver("not-a-version") is None

    def test_partial(self):
        assert _parse_semver("v1.2") is None


class TestVersionNameFor:
    """Test version naming using a mocked repo."""

    def _repo_with_tags(self, tag_names: list[str]) -> GitRepo:
        with patch("latex_builder.git.gitpython.Repo") as MockRepo:
            mock = MockRepo.return_value
            mock.head.is_detached = False
            mock.active_branch.name = "main"
            tags = []
            for name in tag_names:
                t = MagicMock()
                t.name = name
                t.commit.hexsha = f"{'0' * 40}"
                tags.append(t)
            mock.tags = tags
            return GitRepo.__new__(GitRepo)  # bypass __init__
            # We need to set attributes manually
        repo = GitRepo.__new__(GitRepo)
        repo._repo = mock
        repo._tag_map = None
        repo.path = Path(".")
        return repo

    def _make_repo(self, tag_names: list[str]) -> GitRepo:
        mock = MagicMock()
        tags = []
        for name in tag_names:
            t = MagicMock()
            t.name = name
            t.commit.hexsha = "0" * 40
            tags.append(t)
        mock.tags = tags

        repo = GitRepo.__new__(GitRepo)
        repo._repo = mock
        repo._tag_map = None
        repo.path = Path(".")
        return repo

    def test_tagged_no_snapshot(self):
        import datetime
        from datetime import timezone

        repo = self._make_repo(["v1.0.0"])
        rev = Revision(
            commit_hash="abcdef1234567890",
            tag="v1.0.0",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        name = repo.version_name_for(rev)
        assert name.startswith("v1.0.0-abcdef1")
        assert "snapshot" not in name

    def test_untagged_has_snapshot(self):
        import datetime
        from datetime import timezone

        repo = self._make_repo(["v1.0.0"])
        rev = Revision(
            commit_hash="abcdef1234567890",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        name = repo.version_name_for(rev)
        assert "snapshot" in name
        assert "v1.0.1" in name

    def test_dirty_suffix(self):
        import datetime
        from datetime import timezone

        repo = self._make_repo([])
        rev = Revision(
            commit_hash="abcdef1234567890",
            is_dirty=True,
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        name = repo.version_name_for(rev)
        assert "dirty" in name

    def test_no_tags_starts_at_0_0_1(self):
        import datetime
        from datetime import timezone

        repo = self._make_repo([])
        rev = Revision(
            commit_hash="abcdef1234567890",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        name = repo.version_name_for(rev)
        assert "v0.0.1" in name


# =====================================================================
# Integration tests (real Git repos from fixtures)
# =====================================================================

class TestCurrentRevision:
    def test_has_commit_hash(self, git_repo):
        rev = GitRepo(git_repo).current_revision()
        assert len(rev.commit_hash) == 40

    def test_has_branch(self, git_repo):
        rev = GitRepo(git_repo).current_revision()
        assert rev.branch is not None

    def test_author_info(self, git_repo):
        rev = GitRepo(git_repo).current_revision()
        assert rev.author_name == "Test User"

    def test_summary(self, git_repo):
        rev = GitRepo(git_repo).current_revision()
        assert rev.summary == "Second commit"

    def test_version_name(self, git_repo):
        rev = GitRepo(git_repo).current_revision()
        assert rev.version_name is not None
        assert "snapshot" in rev.version_name


class TestPreviousCommit:
    def test_returns_parent(self, git_repo):
        prev = GitRepo(git_repo).previous_commit()
        assert prev is not None
        assert prev.summary == "First commit"

    def test_single_commit_returns_none(self, git_repo_single):
        assert GitRepo(git_repo_single).previous_commit() is None


class TestPreviousTag:
    def test_finds_tag(self, git_repo):
        tag_rev = GitRepo(git_repo).previous_tag()
        assert tag_rev is not None
        assert tag_rev.tag == "v0.1.0"

    def test_no_tags(self, git_repo_no_tags):
        assert GitRepo(git_repo_no_tags).previous_tag() is None


class TestAutoCompareTarget:
    def test_prefers_tag(self, git_repo):
        target = GitRepo(git_repo).auto_compare_target()
        assert target is not None
        assert target.tag == "v0.1.0"

    def test_falls_back_to_parent(self, git_repo_no_tags):
        target = GitRepo(git_repo_no_tags).auto_compare_target()
        assert target is not None
        assert target.summary == "First"


class TestRevisionForRef:
    def test_by_tag(self, git_repo):
        rev = GitRepo(git_repo).revision_for_ref("v0.1.0")
        assert rev is not None
        assert rev.tag == "v0.1.0"

    def test_nonexistent(self, git_repo):
        assert GitRepo(git_repo).revision_for_ref("nonexistent") is None


class TestLatestSemverTag:
    def test_single(self, git_repo):
        assert GitRepo(git_repo)._latest_semver_tag() == "v0.1.0"

    def test_multi(self, git_repo_multi_tags):
        assert GitRepo(git_repo_multi_tags)._latest_semver_tag() == "v1.0.0"

    def test_none(self, git_repo_no_tags):
        assert GitRepo(git_repo_no_tags)._latest_semver_tag() is None


class TestDirty:
    def test_clean(self, git_repo):
        assert GitRepo(git_repo).is_dirty is False

    def test_dirty(self, git_repo):
        (git_repo / "main.tex").write_text("changed")
        assert GitRepo(git_repo).is_dirty is True


class TestWriteRevisionTex:
    def test_creates_file(self, git_repo, tmp_path):
        repo = GitRepo(git_repo)
        rev = repo.current_revision()
        out = tmp_path / "revision.tex"
        repo.write_revision_tex(rev, out)
        assert out.exists()
        content = out.read_text()
        assert r"\newcommand{\GitCommit}" in content
        assert r"\newcommand{\GitRevision}" in content

    def test_creates_parent_dirs(self, git_repo, tmp_path):
        repo = GitRepo(git_repo)
        rev = repo.current_revision()
        out = tmp_path / "deep" / "dir" / "revision.tex"
        repo.write_revision_tex(rev, out)
        assert out.exists()


class TestCheckoutTo:
    def test_checkout(self, git_repo, tmp_path):
        repo = GitRepo(git_repo)
        rev = repo.current_revision()
        dest = tmp_path / "checkout"
        repo.checkout_to(rev.commit_hash, dest)
        assert (dest / "main.tex").exists()

    def test_checkout_older(self, git_repo, tmp_path):
        repo = GitRepo(git_repo)
        prev = repo.previous_commit()
        dest = tmp_path / "old"
        repo.checkout_to(prev.commit_hash, dest)
        content = (dest / "main.tex").read_text()
        assert "v1" in content


class TestInvalidRepo:
    def test_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Not a valid Git repository"):
            GitRepo(tmp_path / "nonexistent")
