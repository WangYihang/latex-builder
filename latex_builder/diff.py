"""Diff generation orchestration."""

from __future__ import annotations

import json
import shutil
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from latex_builder import compiler, log
from latex_builder.config import Config
from latex_builder.git import GitRepo
from latex_builder.revision import Revision

logger = log.get(__name__)


# ------------------------------------------------------------------
# Public workflows
# ------------------------------------------------------------------

def build_and_diff(repo: GitRepo, current: Revision, compare: Revision, cfg: Config) -> None:
    """Full workflow: build current PDF + generate diff PDF + metadata."""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    _build_current(repo, current, cfg)
    _build_diff(repo, current, compare, cfg)
    _write_metadata(current, compare, cfg)


def build_only(repo: GitRepo, current: Revision, cfg: Config) -> None:
    """Build only the current version PDF."""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    _build_current(repo, current, cfg)


def diff_only(repo: GitRepo, current: Revision, compare: Revision, cfg: Config) -> None:
    """Generate only the diff .tex file (no PDF compilation)."""
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    with _playground() as tmp:
        cur_dir, cmp_dir = _checkout_pair(repo, current, compare, tmp, cfg)
        diff_name = _diff_stem(compare, current) + ".tex"
        compiler.latexdiff(
            cmp_dir / cfg.tex_file,
            cur_dir / cfg.tex_file,
            cfg.output_dir / diff_name,
        )


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _build_current(repo: GitRepo, rev: Revision, cfg: Config) -> None:
    repo.write_revision_tex(rev, cfg.repo_path / cfg.revision_file)
    compiler.build(
        cfg.tex_file,
        working_dir=cfg.repo_path,
        output_dir=cfg.output_dir,
        output_name=f"{rev.display_name}.pdf",
        compiler=cfg.compiler,
        timeout=cfg.timeout,
    )


def _build_diff(repo: GitRepo, current: Revision, compare: Revision, cfg: Config) -> None:
    with _playground() as tmp:
        cur_dir, cmp_dir = _checkout_pair(repo, current, compare, tmp, cfg)
        stem = _diff_stem(compare, current)

        compiler.latexdiff(
            cmp_dir / cfg.tex_file,
            cur_dir / cfg.tex_file,
            cmp_dir / f"{stem}.tex",
        )
        compiler.build(
            f"{stem}.tex",
            working_dir=cmp_dir,
            output_dir=cfg.output_dir,
            output_name=f"{stem}.pdf",
            compiler=cfg.compiler,
            timeout=cfg.timeout,
        )


def _checkout_pair(
    repo: GitRepo, current: Revision, compare: Revision, tmp: Path, cfg: Config,
) -> tuple[Path, Path]:
    """Checkout both revisions into *tmp* and generate revision.tex in each."""
    cur_dir = tmp / "current"
    cmp_dir = tmp / "compare"
    repo.checkout_to(current.commit_hash, cur_dir)
    repo.checkout_to(compare.commit_hash, cmp_dir)

    for rev, d in [(current, cur_dir), (compare, cmp_dir)]:
        dest = d / cfg.revision_file
        dest.parent.mkdir(parents=True, exist_ok=True)
        GitRepo(d).write_revision_tex(rev, dest)

    return cur_dir, cmp_dir


def _diff_stem(compare: Revision, current: Revision) -> str:
    return f"{compare.display_name}-vs-{current.display_name}"


@contextmanager
def _playground() -> Iterator[Path]:
    """Temporary directory that is always cleaned up."""
    tmp = Path(tempfile.mkdtemp(prefix="latex-builder-"))
    try:
        yield tmp
    finally:
        try:
            shutil.rmtree(tmp)
        except OSError as exc:
            logger.warning("cleanup failed", path=str(tmp), error=str(exc))


def _write_metadata(current: Revision, compare: Revision, cfg: Config) -> None:
    def _rev_dict(r: Revision) -> dict:
        return {
            "commit": {"hash": r.commit_hash, "short_hash": r.short_hash, "summary": r.summary, "date": r.iso_date},
            "author": {"name": r.author_name, "email": r.author_email},
            "version": {"display_name": r.display_name, "tag": r.tag, "is_dirty": r.is_dirty},
            "branch": r.branch,
        }

    meta = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "settings": {"tex_file": cfg.tex_file, "compiler": cfg.compiler.value, "timeout": cfg.timeout},
        "current": _rev_dict(current),
        "compare": _rev_dict(compare),
        "diff_files": {
            "tex": f"{_diff_stem(compare, current)}.tex",
            "pdf": f"{_diff_stem(compare, current)}.pdf",
        },
    }
    dest = cfg.output_dir / "metadata.json"
    dest.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    logger.info("metadata written", path=str(dest))
