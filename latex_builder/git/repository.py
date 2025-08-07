"""Git repository operations and utilities."""

import os
import shutil
import time
import datetime
from pathlib import Path
from typing import Optional, Union

import git
import semver

from latex_builder.git.revision import GitRevision
from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


class GitRepository:
    """Git repository operations."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize Git repository.

        Args:
            repo_path: Path to Git repository (default: current directory)
        """
        self.repo_path = repo_path or Path.cwd()
        logger.info("Initializing Git repository", path=str(self.repo_path))

        try:
            self.repo = git.Repo(self.repo_path)
            logger.info(
                "Git repository initialized successfully",
                path=str(self.repo_path),
                active_branch=self.repo.active_branch.name if not self.repo.head.is_detached else "detached",
            )
        except Exception as e:
            logger.error(
                "Git repository initialization failed",
                path=str(self.repo_path),
                error=str(e),
            )
            raise ValueError(f"Error initializing Git repository: {repr(e)}")

    def is_working_tree_dirty(self) -> bool:
        """Check if working tree has uncommitted changes.
        
        Returns:
            True if working tree is dirty, False otherwise
        """
        try:
            return self.repo.is_dirty()
        except Exception as e:
            logger.warning(f"Failed to check working tree status: {e}")
            return False

    def parse_semver(self, version: str) -> Optional[semver.Version]:
        """Parse semantic version string using semver library.
        
        Args:
            version: Version string (e.g., "v1.2.3")
            
        Returns:
            semver.Version object or None if invalid
        """
        try:
            # Remove 'v' prefix if present
            if version.startswith('v'):
                version = version[1:]
            
            return semver.Version.parse(version)
        except ValueError:
            return None

    def bump_patch(self, version: str) -> str:
        """Bump patch version using semver library.
        
        Args:
            version: Version string (e.g., "v1.2.3")
            
        Returns:
            Bumped version string
        """
        parsed = self.parse_semver(version)
        if parsed:
            bumped = parsed.bump_patch()
            return f"v{bumped}"
        return "v0.0.1"  # Fallback

    def get_latest_semver_tag(self) -> Optional[str]:
        """Get the latest semantic version tag.
        
        Returns:
            Latest semantic version tag or None if not found
        """
        try:
            tags = self.repo.tags
            semver_tags = []
            
            for tag in tags:
                tag_name = tag.name
                if self.parse_semver(tag_name):
                    semver_tags.append(tag_name)
            
            if not semver_tags:
                return None
            
            # Sort by semantic version using semver library
            semver_tags.sort(key=lambda x: self.parse_semver(x) or semver.Version.parse("0.0.0"))
            return semver_tags[-1]
            
        except Exception as e:
            logger.warning(f"Failed to get latest semver tag: {e}")
            return None

    def generate_version_name(self, revision: GitRevision) -> str:
        """Generate version name according to GoReleaser-like logic.
        
        Args:
            revision: GitRevision object
            
        Returns:
            Generated version name
        """
        # Get latest semantic version tag
        latest_tag = self.get_latest_semver_tag()
        
        if revision.tag_name:
            # Current commit is a tag
            base_version = revision.tag_name
            commit_hash = revision.commit_hash[:7]
        else:
            # Current commit is not a tag, bump version
            if latest_tag:
                next_version = self.bump_patch(latest_tag)
            else:
                next_version = "v0.0.1"  # Start from v0.0.1
            
            base_version = next_version
            commit_hash = revision.commit_hash[:7]
        
        # Add UTC timestamp if available
        timestamp_suffix = ""
        if revision.timestamp:
            # Format timestamp as UTC in ISO format without microseconds
            utc_timestamp = revision.timestamp.strftime("%Y%m%d%H%M%S")
            timestamp_suffix = f"-{utc_timestamp}"

        # Build version name with proper ordering
        if revision.tag_name:
            # Tag version: v1.2.3-commit-timestamp
            version_parts = [base_version, commit_hash]
        else:
            # Non-tag version: v1.2.4-snapshot-commit-timestamp
            version_parts = [base_version, "snapshot", commit_hash]
        
        # Add dirty suffix if working directory is dirty
        if revision.is_dirty:
            version_parts.append("dirty")
        
        # Add timestamp suffix
        version_parts.append(timestamp_suffix.lstrip("-"))
        
        return "-".join(version_parts)

    def get_current_revision(self) -> GitRevision:
        """Get current Git revision.

        Returns:
            GitRevision object for current HEAD
        """
        logger.info("Getting current Git revision")
        commit = self.repo.head.commit
        commit_date = datetime.datetime.fromtimestamp(commit.authored_date).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        logger.info(
            "Current commit found",
            hash=commit.hexsha[:7],
            summary=commit.summary,
            author=commit.author.name,
            date=commit_date,
        )

        tag_name = self._find_tag_for_commit(commit)
        if tag_name:
            logger.info("Tag found for current commit", tag=tag_name)
        else:
            logger.debug("No tags associated with current commit")

        branch_name = None
        try:
            branch_name = self.repo.active_branch.name
            logger.info(f"  • Current branch: {branch_name}")
        except (git.GitCommandError, TypeError):
            logger.info("  • HEAD is in detached state")

        # If no tag, use branch name
        ref_name = None
        if not tag_name:
            try:
                ref_name = self.repo.active_branch.name
            except (git.GitCommandError, TypeError):
                ref_name = "detached-head"
                logger.info(f"  • Using reference name: {ref_name}")

        # Check if working tree is dirty
        is_dirty = self.is_working_tree_dirty()
        if is_dirty:
            logger.info("  • Working tree is dirty (has uncommitted changes)")
        else:
            logger.info("  • Working tree is clean")

        # Convert commit timestamp to UTC datetime
        commit_timestamp = datetime.datetime.utcfromtimestamp(commit.authored_date)

        revision = GitRevision(
            commit_hash=commit.hexsha,
            tag_name=tag_name,
            ref_name=ref_name,
            branch_name=branch_name,
            is_dirty=is_dirty,
            timestamp=commit_timestamp,
            # Additional commit details
            author_name=commit.author.name,
            author_email=commit.author.email,
            commit_summary=commit.summary,
            commit_message=commit.message,
            commit_date=datetime.datetime.utcfromtimestamp(commit.authored_date),
            commit_date_iso=datetime.datetime.utcfromtimestamp(commit.authored_date).isoformat(),
        )

        # Generate version name
        revision.version_name = self.generate_version_name(revision)
        logger.info(f"  • Version name: {revision.version_name}")
        logger.info(f"  • Display name: {revision.display_name}")
        return revision

    def get_previous_commit(self) -> Optional[GitRevision]:
        """
        Get the parent of the current commit.

        Returns:
            GitRevision for parent commit or None if no parent
        """
        logger.info("STEP 3: Identifying parent commit")
        current = self.repo.head.commit
        logger.info(f"  • Current commit: {current.hexsha[:7]}")

        if not current.parents:
            logger.warning(
                "  • No parent commits found (this appears to be the initial commit)"
            )
            return None

        previous = current.parents[0]
        logger.info(
            f"  • Parent commit found: {previous.hexsha[:7]} - {previous.summary}"
        )
        logger.info(
            f"  • Authored by: {previous.author.name} on "
            f"{datetime.datetime.fromtimestamp(previous.authored_date).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        tag_name = self._find_tag_for_commit(previous)
        if tag_name:
            logger.info(f"  • Tag found on parent: {tag_name}")
        else:
            logger.info("  • No tags associated with parent commit")

        # Convert commit timestamp to UTC datetime
        commit_timestamp = datetime.datetime.utcfromtimestamp(previous.authored_date)

        revision = GitRevision(
            commit_hash=previous.hexsha, 
            tag_name=tag_name,
            timestamp=commit_timestamp,
            # Additional commit details
            author_name=previous.author.name,
            author_email=previous.author.email,
            commit_summary=previous.summary,
            commit_message=previous.message,
            commit_date=datetime.datetime.utcfromtimestamp(previous.authored_date),
            commit_date_iso=datetime.datetime.utcfromtimestamp(previous.authored_date).isoformat(),
        )
        
        # Generate version name
        revision.version_name = self.generate_version_name(revision)
        logger.info(f"  • Version name: {revision.version_name}")
        logger.info(f"  • Display name: {revision.display_name}")
        
        return revision

    def get_previous_tag(self) -> Optional[GitRevision]:
        """
        Get the most recent tag before the current commit.

        Returns:
            GitRevision for the previous tag or None if no tags
        """
        logger.info("STEP 4: Finding previous tagged version")
        try:
            current = self.repo.head.commit
            logger.info(f"  • Current commit: {current.hexsha[:7]}")

            # Get all tags
            all_tags = list(self.repo.tags)
            logger.info(f"  • Found {len(all_tags)} tags in the repository")

            if not all_tags:
                logger.warning("  • No tags found in the repository")
                return None

            # Sort tags by commit date (newest first)
            sorted_tags = sorted(
                all_tags, key=lambda t: t.commit.committed_datetime, reverse=True
            )

            logger.info("  • Tags sorted by commit date (showing up to 5):")
            for idx, tag in enumerate(sorted_tags[:5]):
                commit_date = tag.commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(
                    f"    {idx + 1}. {tag.name} - {tag.commit.hexsha[:7]} ({commit_date})"
                )

            for tag in sorted_tags:
                if tag.commit != current:
                    logger.info(
                        f"  • Selected previous tag: {tag.name} ({tag.commit.hexsha[:7]})"
                    )
                    # Convert commit timestamp to UTC datetime
                    commit_timestamp = datetime.datetime.utcfromtimestamp(tag.commit.authored_date)
                    revision = GitRevision(
                        commit_hash=tag.commit.hexsha, 
                        tag_name=tag.name,
                        timestamp=commit_timestamp,
                        # Additional commit details
                        author_name=tag.commit.author.name,
                        author_email=tag.commit.author.email,
                        commit_summary=tag.commit.summary,
                        commit_message=tag.commit.message,
                        commit_date=datetime.datetime.utcfromtimestamp(tag.commit.authored_date),
                        commit_date_iso=datetime.datetime.utcfromtimestamp(tag.commit.authored_date).isoformat(),
                    )
                    
                    # Generate version name
                    revision.version_name = self.generate_version_name(revision)
                    logger.info(f"  • Version name: {revision.version_name}")
                    logger.info(f"  • Display name: {revision.display_name}")
                    
                    return revision

            # If all tags point to current commit, return None
            logger.info(
                "  • All tags point to current commit, no previous tag available"
            )
            return None

        except Exception as e:
            logger.warning(f"  • Error finding previous tag: {repr(e)}")
            logger.warning("  • Falling back to parent commit")
            previous = self.get_previous_commit()
            if previous:
                return previous
            else:
                # Convert commit timestamp to UTC datetime
                commit_timestamp = datetime.datetime.utcfromtimestamp(self.repo.head.commit.authored_date)
                revision = GitRevision(
                    commit_hash=self.repo.head.commit.hexsha,
                    timestamp=commit_timestamp,
                    # Additional commit details
                    author_name=self.repo.head.commit.author.name,
                    author_email=self.repo.head.commit.author.email,
                    commit_summary=self.repo.head.commit.summary,
                    commit_message=self.repo.head.commit.message,
                    commit_date=datetime.datetime.utcfromtimestamp(self.repo.head.commit.authored_date),
                    commit_date_iso=datetime.datetime.utcfromtimestamp(self.repo.head.commit.authored_date).isoformat(),
                )
                
                # Generate version name
                revision.version_name = self.generate_version_name(revision)
                logger.info(f"  • Version name: {revision.version_name}")
                logger.info(f"  • Display name: {revision.display_name}")
                
                return revision

    def get_revision_by_ref(self, ref: str) -> Optional[GitRevision]:
        """
        Get GitRevision for a specific reference (tag, commit hash, or branch).

        Args:
            ref: Git reference (tag name, commit hash, or branch name)

        Returns:
            GitRevision object or None if reference not found
        """
        logger.info(f"Looking up reference: {ref}")

        try:
            # Try to resolve the reference
            commit = self.repo.commit(ref)
            logger.info(f"  • Found commit: {commit.hexsha[:7]} - {commit.summary}")

            # Check if it's a tag
            tag_name = self._find_tag_for_commit(commit)
            if tag_name:
                logger.info(f"  • Reference is a tag: {tag_name}")

            # Convert commit timestamp to UTC datetime
            commit_timestamp = datetime.datetime.utcfromtimestamp(commit.authored_date)

            revision = GitRevision(
                commit_hash=commit.hexsha, 
                tag_name=tag_name,
                timestamp=commit_timestamp,
                # Additional commit details
                author_name=commit.author.name,
                author_email=commit.author.email,
                commit_summary=commit.summary,
                commit_message=commit.message,
                commit_date=datetime.datetime.utcfromtimestamp(commit.authored_date),
                commit_date_iso=datetime.datetime.utcfromtimestamp(commit.authored_date).isoformat(),
            )
            
            # Generate version name
            revision.version_name = self.generate_version_name(revision)
            logger.info(f"  • Version name: {revision.version_name}")
            logger.info(f"  • Display name: {revision.display_name}")
            
            return revision

        except (git.GitCommandError, git.BadName) as e:
            logger.warning(f"  • Reference '{ref}' not found: {str(e)}")
            return None

    def _find_tag_for_commit(self, commit) -> Optional[str]:
        """
        Find tag name for a commit.

        Args:
            commit: Git commit object

        Returns:
            Tag name or None if no tag
        """
        logger.debug(f"Searching for tags on commit {commit.hexsha[:7]}")
        for tag in self.repo.tags:
            if tag.commit == commit:
                logger.debug(f"  • Found tag: {tag.name}")
                return tag.name
        logger.debug(f"  • No tags found for commit {commit.hexsha[:7]}")
        return None

    def generate_revision_file(self, revision: GitRevision, output_path: Path) -> None:
        """
        Generate a revision.tex file with git version information.

        Args:
            revision: GitRevision object
            output_path: Path where to save the revision.tex file
        """
        logger.info("STEP 5: Generating revision information file")
        logger.info(f"  • Revision: {revision.display_name}")
        logger.info(f"  • Output path: {output_path}")

        try:
            # Create output directory if it doesn't exist
            if not output_path.parent.exists():
                logger.info(f"  • Creating directory: {output_path.parent}")
                output_path.parent.mkdir(parents=True, exist_ok=True)

            """
            \newcommand{\GitCommit}{1b7cec2}
            \newcommand{\GitTag}{v0.0.1}
            \newcommand{\GitBranch}{main}
            \newcommand{\GitRevision}{1b7cec2-v0.0.1-main}
            \newcommand{\CompiledDate}{2023-10-01T12:00:00Z}
            """

            data = {
                "GitCommit": revision.commit_hash[0:7],
                "GitTag": revision.tag_name or "",
                "GitBranch": revision.branch_name,
                "GitRevision": revision.display_name,
                "CompiledDate": datetime.datetime.now().isoformat(),
            }

            logger.info("  • Writing the following data to revision file:")
            for key, value in data.items():
                logger.info(f"    - {key}: {value}")

            # Write the revision.tex file
            with open(output_path, "w") as f:
                f.write(
                    "\n".join(
                        f"\\newcommand{{\\{key}}}{{{value}}}"
                        for key, value in data.items()
                    )
                )

            logger.info(f"  • Successfully generated revision.tex at {output_path}")
        except Exception as e:
            logger.error(f"  • Failed to generate revision.tex: {repr(e)}")
            raise RuntimeError(f"Failed to generate revision.tex: {repr(e)}")

    def checkout_revision(
        self, revision: Union[GitRevision, str], target_dir: Path
    ) -> None:
        """
        Checkout a specific Git revision to a target directory.

        Args:
            revision: GitRevision object or commit hash string
            target_dir: Directory where to checkout the revision

        Raises:
            RuntimeError: If checkout fails
        """
        start_time = time.time()

        # Get commit hash if GitRevision object
        commit_hash = (
            revision.commit_hash if isinstance(revision, GitRevision) else revision
        )
        rev_display = (
            revision.display_name
            if isinstance(revision, GitRevision)
            else commit_hash[:7]
        )

        logger.info(f"STEP 6: Checking out revision {rev_display}")
        logger.info(f"  • Target directory: {target_dir}")

        try:
            # Create target directory if it doesn't exist
            if not target_dir.exists():
                logger.info(f"  • Creating target directory: {target_dir}")
                target_dir.mkdir(parents=True, exist_ok=True)

            # Copy .git directory to target
            git_dir = self.repo_path / ".git"
            target_git_dir = target_dir / ".git"

            logger.info("  • Copying Git repository to target")
            if target_git_dir.exists():
                logger.info(f"  • Removing existing .git directory: {target_git_dir}")
                shutil.rmtree(target_git_dir)

            logger.info(f"  • Copying .git from {git_dir} to {target_git_dir}")
            shutil.copytree(git_dir, target_git_dir)

            # Change to target directory
            original_cwd = os.getcwd()
            logger.info(f"  • Current working directory: {original_cwd}")
            logger.info(f"  • Changing to target directory: {target_dir}")

            try:
                os.chdir(target_dir)

                # Create a new repo object for the target directory
                logger.info("  • Initializing repository in target directory")
                repo = git.Repo(".")

                # Reset and checkout the revision
                logger.info("  • Resetting repository to HEAD")
                repo.git.reset("--hard", "HEAD")

                logger.info(f"  • Checking out commit: {commit_hash[:7]}")
                repo.git.checkout(commit_hash)

                end_time = time.time()
                duration = end_time - start_time
                logger.info(
                    f"  • Successfully checked out {commit_hash[:7]} (took {duration:.2f} seconds)"
                )
            finally:
                # Return to original directory
                logger.info(f"  • Returning to original directory: {original_cwd}")
                os.chdir(original_cwd)
        except Exception as e:
            error_msg = f"Failed to checkout revision {commit_hash}: {repr(e)}"
            logger.error(f"  • {error_msg}")
            raise RuntimeError(error_msg)
