"""Tests for latex_builder.diff orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from latex_builder.config import Config
from latex_builder.diff import _write_metadata, build_only
from latex_builder.revision import Revision


class TestWriteMetadata:
    def test_creates_file(self, tmp_path, sample_rev, compare_rev):
        cfg = Config(output_dir=tmp_path)
        _write_metadata(sample_rev, compare_rev, cfg)
        assert (tmp_path / "metadata.json").exists()

    def test_structure(self, tmp_path, sample_rev, compare_rev):
        cfg = Config(output_dir=tmp_path)
        _write_metadata(sample_rev, compare_rev, cfg)
        meta = json.loads((tmp_path / "metadata.json").read_text())
        assert "generated_at" in meta
        assert "current" in meta
        assert "compare" in meta
        assert "diff_files" in meta

    def test_revision_info(self, tmp_path, sample_rev, compare_rev):
        cfg = Config(output_dir=tmp_path)
        _write_metadata(sample_rev, compare_rev, cfg)
        meta = json.loads((tmp_path / "metadata.json").read_text())
        assert meta["current"]["commit"]["hash"] == sample_rev.commit_hash
        assert meta["compare"]["commit"]["hash"] == compare_rev.commit_hash


class TestBuildOnly:
    @patch("latex_builder.diff.compiler.build")
    @patch("latex_builder.diff.GitRepo.write_revision_tex")  # called on the passed repo
    def test_calls_compiler(self, mock_write, mock_build, tmp_path, sample_rev):
        repo = MagicMock()
        repo.write_revision_tex = mock_write
        cfg = Config(repo_path=tmp_path, output_dir=tmp_path / "out")
        build_only(repo, sample_rev, cfg)
        mock_build.assert_called_once()
