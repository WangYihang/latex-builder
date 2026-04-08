"""Tests for latex_builder.revision."""

import datetime
from datetime import timezone

from latex_builder.revision import Revision


class TestShortHash:
    def test_first_7_chars(self):
        assert Revision(commit_hash="abcdef1234567890").short_hash == "abcdef1"

    def test_full_40_char_hash(self):
        assert Revision(commit_hash="a" * 40).short_hash == "aaaaaaa"


class TestDisplayName:
    def test_version_name_wins(self):
        r = Revision(commit_hash="abc1234567", tag="v1", version_name="v1.0.0-abc1234")
        assert r.display_name == "v1.0.0-abc1234"

    def test_tag_fallback(self):
        r = Revision(commit_hash="abc1234567", tag="v1.0.0")
        assert r.display_name == "v1.0.0"

    def test_branch_fallback(self):
        r = Revision(commit_hash="abc1234567", branch="main")
        assert r.display_name == "main"

    def test_hash_fallback(self):
        r = Revision(commit_hash="abc1234567")
        assert r.display_name == "abc1234"


class TestIsoDate:
    def test_with_timestamp(self):
        ts = datetime.datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        assert Revision(commit_hash="a" * 40, timestamp=ts).iso_date == ts.isoformat()

    def test_without_timestamp(self):
        assert Revision(commit_hash="a" * 40).iso_date is None


class TestWithVersionName:
    def test_returns_new_instance(self):
        r = Revision(commit_hash="abc", tag="v1")
        r2 = r.with_version_name("v1.0.0-abc")
        assert r2 is not r
        assert r2.version_name == "v1.0.0-abc"
        assert r2.tag == "v1"
        assert r.version_name is None  # original unchanged


class TestDefaults:
    def test_only_hash_required(self):
        r = Revision(commit_hash="abc")
        assert r.tag is None
        assert r.branch is None
        assert r.is_dirty is False
        assert r.version_name is None
        assert r.timestamp is None
        assert r.iso_date is None

    def test_immutable(self):
        r = Revision(commit_hash="abc")
        try:
            r.tag = "v1"  # type: ignore[misc]
            assert False, "Should be frozen"
        except AttributeError:
            pass
