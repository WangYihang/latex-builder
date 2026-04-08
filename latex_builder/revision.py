"""Git revision data model."""

from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Revision:
    """Immutable snapshot of a Git revision."""

    commit_hash: str
    tag: str | None = None
    branch: str | None = None
    is_dirty: bool = False
    timestamp: datetime.datetime | None = None
    author_name: str | None = None
    author_email: str | None = None
    summary: str | None = None
    message: str | None = None
    version_name: str | None = None

    @property
    def short_hash(self) -> str:
        return self.commit_hash[:7]

    @property
    def display_name(self) -> str:
        return self.version_name or self.tag or self.branch or self.short_hash

    @property
    def iso_date(self) -> str | None:
        return self.timestamp.isoformat() if self.timestamp else None

    def with_version_name(self, name: str) -> Revision:
        """Return a copy with version_name set (since we're frozen)."""
        return Revision(
            commit_hash=self.commit_hash,
            tag=self.tag,
            branch=self.branch,
            is_dirty=self.is_dirty,
            timestamp=self.timestamp,
            author_name=self.author_name,
            author_email=self.author_email,
            summary=self.summary,
            message=self.message,
            version_name=name,
        )
