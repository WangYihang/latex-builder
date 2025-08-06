"""Git revision data structures and utilities."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GitRevision:
    """Represents a Git revision with associated information."""

    commit_hash: str
    tag_name: Optional[str] = None
    branch_name: Optional[str] = None
    ref_name: Optional[str] = None

    @property
    def short_hash(self) -> str:
        """Return shortened commit hash."""
        return self.commit_hash[:7]

    @property
    def display_name(self) -> str:
        """Return a human-readable display name for the revision."""
        # Start with the most specific identifier
        if self.tag_name:
            prefix = [self.tag_name]
        elif self.ref_name:
            prefix = [self.ref_name]
        else:
            prefix = []

        # Add branch name if available and not already included
        if self.branch_name and self.branch_name not in prefix:
            prefix.append(self.branch_name)

        # Join all parts and add short hash
        if prefix:
            return f"{'-'.join(prefix)}-{self.short_hash}"
        return self.short_hash
