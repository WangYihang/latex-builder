"""Git repository operations."""

from __future__ import annotations

import datetime
import shutil
import time
from datetime import timezone
from pathlib import Path

import git as gitpython
import semver

from latex_builder import log
from latex_builder.revision import Revision

logger = log.get(__name__)


class GitRepo:
    """Thin wrapper around a Git repository."""

    def __init__(self, path: Path) -> None:
        self.path = path
        try:
            self._repo = gitpython.Repo(path)
        except Exception as exc:
            raise ValueError(f"Not a valid Git repository: {path}") from exc

        self._tag_map: dict[str, str] | None = None  # commit_hex -> tag_name

    # ------------------------------------------------------------------
    # Public queries
    # ------------------------------------------------------------------

    @property
    def is_dirty(self) -> bool:
        try:
            return self._repo.is_dirty()
        except Exception:
            return True  # assume dirty on error

    def current_revision(self) -> Revision:
        """Build a Revision for the current HEAD."""
        commit = self._repo.head.commit
        tag = self._tag_for(commit)
        branch = self._active_branch()

        rev = self._make_revision(commit, tag=tag, branch=branch, is_dirty=self.is_dirty)
        logger.info("current revision", version=rev.display_name, dirty=rev.is_dirty)
        return rev

    def revision_for_ref(self, ref: str) -> Revision | None:
        """Resolve a tag / branch / commit-hash to a Revision."""
        try:
            commit = self._repo.commit(ref)
        except (gitpython.GitCommandError, gitpython.BadName):
            logger.warning("ref not found", ref=ref)
            return None
        return self._make_revision(commit, tag=self._tag_for(commit))

    def previous_tag(self) -> Revision | None:
        """Most recent tag that does NOT point at HEAD."""
        current = self._repo.head.commit
        tags = sorted(self._repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
        for t in tags:
            if t.commit != current:
                return self._make_revision(t.commit, tag=t.name)
        return None

    def previous_commit(self) -> Revision | None:
        """Parent of HEAD, or None for initial commits."""
        parents = self._repo.head.commit.parents
        if not parents:
            return None
        return self._make_revision(parents[0], tag=self._tag_for(parents[0]))

    def auto_compare_target(self) -> Revision | None:
        """Pick the best comparison target: latest tag > parent commit."""
        return self.previous_tag() or self.previous_commit()

    # ------------------------------------------------------------------
    # Checkout helpers
    # ------------------------------------------------------------------

    def checkout_to(self, commit_hash: str, target: Path) -> None:
        """Copy .git and checkout *commit_hash* into *target*."""
        t0 = time.monotonic()
        target.mkdir(parents=True, exist_ok=True)
        target_git = target / ".git"
        if target_git.exists():
            shutil.rmtree(target_git)
        shutil.copytree(self.path / ".git", target_git)

        repo = gitpython.Repo(target)
        repo.git.reset("--hard", "HEAD")
        repo.git.checkout(commit_hash)
        logger.debug("checkout", hash=commit_hash[:7], seconds=f"{time.monotonic() - t0:.1f}")

    # ------------------------------------------------------------------
    # Revision-file generation
    # ------------------------------------------------------------------

    def write_revision_tex(self, rev: Revision, dest: Path) -> None:
        """Write a revision.tex with LaTeX \\newcommand macros."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            rf"\newcommand{{\GitCommit}}{{{rev.short_hash}}}",
            rf"\newcommand{{\GitTag}}{{{rev.tag or ''}}}",
            rf"\newcommand{{\GitBranch}}{{{rev.branch or ''}}}",
            rf"\newcommand{{\GitRevision}}{{{rev.display_name}}}",
            rf"\newcommand{{\CompiledDate}}{{{datetime.datetime.now(tz=timezone.utc).isoformat()}}}",
        ]
        dest.write_text("\n".join(lines), encoding="utf-8")
        logger.debug("wrote revision.tex", path=str(dest))

    # ------------------------------------------------------------------
    # Version naming (GoReleaser-style)
    # ------------------------------------------------------------------

    def version_name_for(self, rev: Revision) -> str:
        """Generate a GoReleaser-style version string."""
        if rev.tag:
            parts = [rev.tag, rev.short_hash]
        else:
            base = self._next_version()
            parts = [base, "snapshot", rev.short_hash]

        if rev.is_dirty:
            parts.append("dirty")

        if rev.timestamp:
            parts.append(rev.timestamp.strftime("%Y%m%d%H%M%S"))

        return "-".join(parts)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_revision(
        self, commit, *, tag: str | None = None, branch: str | None = None, is_dirty: bool = False,
    ) -> Revision:
        ts = datetime.datetime.fromtimestamp(commit.authored_date, tz=timezone.utc)
        rev = Revision(
            commit_hash=commit.hexsha,
            tag=tag,
            branch=branch,
            is_dirty=is_dirty,
            timestamp=ts,
            author_name=commit.author.name,
            author_email=commit.author.email,
            summary=commit.summary,
            message=commit.message,
        )
        return rev.with_version_name(self.version_name_for(rev))

    def _tag_for(self, commit) -> str | None:
        if self._tag_map is None:
            self._tag_map = {t.commit.hexsha: t.name for t in self._repo.tags}
        return self._tag_map.get(commit.hexsha)

    def _active_branch(self) -> str | None:
        try:
            return self._repo.active_branch.name
        except (gitpython.GitCommandError, TypeError):
            return None

    def _latest_semver_tag(self) -> str | None:
        tags = []
        for t in self._repo.tags:
            v = _parse_semver(t.name)
            if v is not None:
                tags.append((v, t.name))
        if not tags:
            return None
        tags.sort(key=lambda pair: pair[0])
        return tags[-1][1]

    def _next_version(self) -> str:
        latest = self._latest_semver_tag()
        if latest is None:
            return "v0.0.1"
        v = _parse_semver(latest)
        if v is None:
            return "v0.0.1"
        return f"v{v.bump_patch()}"


def _parse_semver(tag: str) -> semver.Version | None:
    raw = tag.lstrip("v")
    try:
        return semver.Version.parse(raw)
    except ValueError:
        return None
