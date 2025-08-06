#!/usr/bin/env python3
"""
A utility for compiling LaTeX documents and generating diffs between Git revisions.
"""

import os
import sys
import shutil
import logging
import subprocess
import json
import argparse
import datetime
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Union

import git
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn


# Configure logging with rich for better output
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("latex-diff")


@dataclass
class Config:
    """Configuration for the LaTeX diff tool."""
    tex_file: str = "main.tex"
    revision_path: str = "miscellaneous/revision.tex"
    verbose: bool = False
    output_folder: Path = Path("output")
    build_dir: Path = Path("build")


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


class GitRepository:
    """Handle Git repository operations."""
    
    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize GitRepository.
        
        Args:
            repo_path: Path to the Git repository, defaults to current directory
        
        Raises:
            ValueError: If the path is not a valid Git repository
        """
        logger.info("STEP 1: Initializing Git repository")
        try:
            self.repo_path = repo_path or Path.cwd()
            logger.info(f"  • Searching for Git repository at: {self.repo_path}")
            self.repo = git.Repo(self.repo_path)
            logger.info(f"  • Successfully initialized Git repository")
            logger.debug(f"  • Repository root: {self.repo.git_dir}")
        except git.InvalidGitRepositoryError:
            logger.error(f"  • Failed: {self.repo_path} is not a valid Git repository")
            raise ValueError(f"{self.repo_path} is not a valid Git repository")
        except Exception as e:
            logger.error(f"  • Failed: Error initializing Git repository: {repr(e)}")
            raise ValueError(f"Error initializing Git repository: {repr(e)}")
    
    def get_current_revision(self) -> GitRevision:
        """
        Get the current Git revision.
        
        Returns:
            GitRevision object for current HEAD
        """
        logger.info("STEP 2: Getting current Git revision")
        commit = self.repo.head.commit
        logger.info(f"  • Current commit: {commit.hexsha[:7]} - {commit.summary}")
        logger.info(f"  • Authored by: {commit.author.name} on {datetime.datetime.fromtimestamp(commit.authored_date).strftime('%Y-%m-%d %H:%M:%S')}")
        
        tag_name = self._find_tag_for_commit(commit)
        if tag_name:
            logger.info(f"  • Tag found: {tag_name}")
        else:
            logger.info(f"  • No tags associated with current commit")
            
        branch_name = None
        try:
            branch_name = self.repo.active_branch.name
            logger.info(f"  • Current branch: {branch_name}")
        except (git.GitCommandError, TypeError):
            logger.info(f"  • HEAD is in detached state")
        
        # If no tag, use branch name
        ref_name = None
        if not tag_name:
            try:
                ref_name = self.repo.active_branch.name
            except (git.GitCommandError, TypeError):
                ref_name = "detached-head"
                logger.info(f"  • Using reference name: {ref_name}")
        
        revision = GitRevision(
            commit_hash=commit.hexsha,
            tag_name=tag_name,
            ref_name=ref_name,
            branch_name=branch_name,
        )
        
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
            logger.warning("  • No parent commits found (this appears to be the initial commit)")
            return None
            
        previous = current.parents[0]
        logger.info(f"  • Parent commit found: {previous.hexsha[:7]} - {previous.summary}")
        logger.info(f"  • Authored by: {previous.author.name} on {datetime.datetime.fromtimestamp(previous.authored_date).strftime('%Y-%m-%d %H:%M:%S')}")
        
        tag_name = self._find_tag_for_commit(previous)
        if tag_name:
            logger.info(f"  • Tag found on parent: {tag_name}")
        else:
            logger.info(f"  • No tags associated with parent commit")
        
        return GitRevision(
            commit_hash=previous.hexsha,
            tag_name=tag_name
        )
    
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
                first_commit = next(self.repo.iter_commits(max_parents=0))
                logger.info(f"  • Using first commit as base: {first_commit.hexsha[:7]}")
                return GitRevision(commit_hash=first_commit.hexsha)
            
            # Sort tags by commit date (newest first)
            sorted_tags = sorted(
                all_tags, 
                key=lambda t: t.commit.committed_datetime, 
                reverse=True
            )
            
            logger.info(f"  • Tags sorted by commit date (showing up to 5):")
            for idx, tag in enumerate(sorted_tags[:5]):
                logger.info(f"    {idx+1}. {tag.name} - {tag.commit.hexsha[:7]} ({tag.commit.committed_datetime.strftime('%Y-%m-%d %H:%M:%S')})")
            
            for tag in sorted_tags:
                if tag.commit != current:
                    logger.info(f"  • Selected previous tag: {tag.name} ({tag.commit.hexsha[:7]})")
                    return GitRevision(
                        commit_hash=tag.commit.hexsha,
                        tag_name=tag.name
                    )
            
            # If all tags point to current commit, use first commit
            logger.info("  • All tags point to current commit, using first commit as base")        
            first_commit = next(self.repo.iter_commits(max_parents=0))
            logger.info(f"  • Using first commit: {first_commit.hexsha[:7]}")
            return GitRevision(commit_hash=first_commit.hexsha)
            
        except Exception as e:
            logger.warning(f"  • Error finding previous tag: {repr(e)}")
            logger.warning("  • Falling back to parent commit")
            previous = self.get_previous_commit()
            return previous if previous else GitRevision(commit_hash=self.repo.head.commit.hexsha)
    
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
        logger.info(f"STEP 5: Generating revision information file")
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
                "CompiledDate": datetime.datetime.now().isoformat()
            }
            
            logger.info(f"  • Writing the following data to revision file:")
            for key, value in data.items():
                logger.info(f"    - {key}: {value}")

            # Write the revision.tex file
            with open(output_path, "w") as f:
                f.write("\n".join(f"\\newcommand{{\\{key}}}{{{value}}}" for key, value in data.items()))

            logger.info(f"  • Successfully generated revision.tex at {output_path}")
        except Exception as e:
            logger.error(f"  • Failed to generate revision.tex: {repr(e)}")
            raise RuntimeError(f"Failed to generate revision.tex: {repr(e)}")
    
    def checkout_revision(self, revision: Union[GitRevision, str], target_dir: Path) -> None:
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
        commit_hash = revision.commit_hash if isinstance(revision, GitRevision) else revision
        rev_display = revision.display_name if isinstance(revision, GitRevision) else commit_hash[:7]
        
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
            
            logger.info(f"  • Copying Git repository to target")
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
                logger.info(f"  • Initializing repository in target directory")
                repo = git.Repo(".")

                # Reset and checkout the revision
                logger.info(f"  • Resetting repository to HEAD")
                repo.git.reset('--hard', 'HEAD')
                
                logger.info(f"  • Checking out commit: {commit_hash[:7]}")
                repo.git.checkout(commit_hash)
                
                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"  • Successfully checked out {commit_hash[:7]} (took {duration:.2f} seconds)")
            finally:
                # Return to original directory
                logger.info(f"  • Returning to original directory: {original_cwd}")
                os.chdir(original_cwd)
        except Exception as e:
            error_msg = f"Failed to checkout revision {commit_hash}: {repr(e)}"
            logger.error(f"  • {error_msg}")
            raise RuntimeError(error_msg)


class LaTeXProcessor:
    """Handles LaTeX document processing operations."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize LaTeXProcessor.
        
        Args:
            base_dir: Base directory for operations, defaults to current directory
        """
        logger.info("STEP 7: Initializing LaTeX processor")
        self.base_dir = base_dir or Path.cwd()
        logger.info(f"  • Base directory: {self.base_dir}")
    
    def build_document(self, 
                      tex_file: str, 
                      working_dir: Optional[Path] = None, 
                      output_folder: Optional[Path] = None, 
                      output_filename: str = "main.pdf") -> None:
        """
        Build a LaTeX document using xelatex and bibtex.
        
        Args:
            tex_file: Name of the .tex file to compile
            working_dir: Directory to run the commands in (defaults to self.base_dir)
            output_folder: Directory where output files will be saved
            output_filename: Name of the output file (without extension)
            
        Raises:
            RuntimeError: If build fails
        """
        logger.info("STEP 8: Building LaTeX document")
        start_time = time.time()
        
        cwd = working_dir or self.base_dir
        output_folder = output_folder or self.base_dir
        
        logger.info(f"  • Building document: {tex_file}")
        logger.info(f"  • Working directory: {cwd}")
        logger.info(f"  • Output folder: {output_folder}")
        logger.info(f"  • Output filename: {output_filename}")
        
        try:
            logger.info(f"  • Starting LaTeX compilation process")
            self._run_latex_commands(tex_file, cwd)
            
            # Copy output PDF file to output folder
            basename = Path(tex_file).stem
            pdf_file = cwd / f"{basename}.pdf"
            
            if pdf_file.exists():
                if not output_folder.exists():
                    logger.info(f"  • Creating output folder: {output_folder}")
                    output_folder.mkdir(parents=True, exist_ok=True)
                
                output_path = output_folder / output_filename
                logger.info(f"  • Copying PDF from {pdf_file} to {output_path}")
                shutil.copy(pdf_file, output_path)
                
                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"  • PDF file copied to {output_path} (total build time: {duration:.2f} seconds)")
            else:
                error_msg = f"PDF file not found: {pdf_file}"
                logger.error(f"  • {error_msg}")
                raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"LaTeX build failed: {repr(e)}"
            logger.error(f"  • {error_msg}")
            raise RuntimeError(error_msg)
    
    def _run_latex_commands(self, tex_file: str, cwd: Path) -> None:
        """
        Run LaTeX commands to compile a document.
        
        Args:
            tex_file: Name of the .tex file to compile
            cwd: Directory to run the commands in
            
        Raises:
            RuntimeError: If any command fails
        """
        basename = Path(tex_file).stem
        
        # Run LaTeX commands
        logger.info(f"  • [1/4] Running first xelatex pass")
        cmd_start = time.time()
        self._run_command(["xelatex", "-shell-escape", tex_file], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • [2/4] Running bibtex")
        cmd_start = time.time()
        self._run_command(["bibtex", basename], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • [3/4] Running second xelatex pass")
        cmd_start = time.time()
        self._run_command(["xelatex", "-shell-escape", tex_file], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • [4/4] Running final xelatex pass")
        cmd_start = time.time()
        self._run_command(["xelatex", "-shell-escape", tex_file], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • Build sequence completed for: {tex_file}")
    
    def generate_diff(self, 
                     original_file: Path, 
                     modified_file: Path, 
                     output_file: Path) -> None:
        """
        Generate LaTeX diff between two files.
        
        Args:
            original_file: Path to the original .tex file
            modified_file: Path to the modified .tex file
            output_file: Path where to save the diff .tex file
            
        Raises:
            RuntimeError: If diff generation fails
        """
        logger.info("STEP 9: Generating LaTeX diff")
        start_time = time.time()
        
        logger.info(f"  • Original file: {original_file}")
        logger.info(f"  • Modified file: {modified_file}")
        logger.info(f"  • Output diff file: {output_file}")
        
        try:
            # Create output directory if it doesn't exist
            if not output_file.parent.exists():
                logger.info(f"  • Creating output directory: {output_file.parent}")
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate diff file
            logger.info(f"  • Running latexdiff with --flatten option")
            result = self._run_command([
                "latexdiff", 
                "--flatten", 
                str(original_file), 
                str(modified_file)
            ])
            
            # Write to output file
            logger.info(f"  • Writing diff output to {output_file}")
            with open(output_file, "w") as f:
                f.write(result)
            
            end_time = time.time()
            duration = end_time - start_time    
            logger.info(f"  • Diff generation completed in {duration:.2f} seconds")
            logger.info(f"  • Output saved to {output_file}")
        except Exception as e:
            error_msg = f"Failed to generate diff: {repr(e)}"
            logger.error(f"  • {error_msg}")
            raise RuntimeError(error_msg)
    
    @staticmethod
    def _run_command(cmd: List[str], cwd: Optional[Path] = None) -> str:
        """
        Execute a shell command and return its output.
        Log stdout and stderr in real-time.
        
        Args:
            cmd: Command to run as a list of strings
            cwd: Directory to run the command in
            
        Returns:
            Command output as string
            
        Raises:
            RuntimeError: If command fails
        """
        cmd_str = ' '.join(cmd)
        logger.debug(f"Running command: {cmd_str}")
        logger.debug(f"Working directory: {cwd}")
        
        try:
            # Use Popen to get real-time output
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Collect output for return value
            stdout_lines = []
            
            # Process stdout and stderr in real-time
            while True:
                stdout_line = process.stdout.readline() if process.stdout else ""
                stderr_line = process.stderr.readline() if process.stderr else ""
                
                if stdout_line:
                    logger.debug(f"[stdout] {stdout_line.rstrip()}")
                    stdout_lines.append(stdout_line)
                    
                if stderr_line:
                    logger.debug(f"[stderr] {stderr_line.rstrip()}")
                
                if not stdout_line and not stderr_line and process.poll() is not None:
                    break
            
            # Get any remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                logger.debug(f"[stdout] {remaining_stdout.rstrip()}")
                stdout_lines.append(remaining_stdout)
            if remaining_stderr:
                logger.debug(f"[stderr] {remaining_stderr.rstrip()}")
            
            # Check return code
            if process.returncode != 0:
                error_msg = f"Command failed with exit code {process.returncode}: {cmd_str}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            return "".join(stdout_lines).strip()
        except Exception as e:
            error_msg = f"Command failed: {cmd_str}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


class DiffGenerator:
    """Handles the generation of LaTeX diffs between Git revisions."""
    
    def __init__(self, 
                git_repo: GitRepository, 
                latex_processor: LaTeXProcessor,
                config: Config):
        """
        Initialize DiffGenerator.
        
        Args:
            git_repo: GitRepository instance
            latex_processor: LaTeXProcessor instance
            config: Configuration object
        """
        logger.info("STEP 10: Initializing Diff Generator")
        self.git_repo = git_repo
        self.latex_processor = latex_processor
        self.config = config
        self.output_folder = config.output_folder
        self.build_dir = config.build_dir
        
        logger.info(f"  • Output folder: {self.output_folder}")
        logger.info(f"  • Build directory: {self.build_dir}")
    
    def generate_diffs(self, 
                      current: GitRevision, 
                      previous_commit: GitRevision, 
                      previous_tag: GitRevision) -> None:
        """
        Generate and build diff files between Git revisions.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
            
        Raises:
            RuntimeError: If any operation fails
        """
        logger.info("STEP 11: Starting diff generation process")
        logger.info(f"  • Current revision: {current.display_name}")
        logger.info(f"  • Previous commit: {previous_commit.display_name}")
        logger.info(f"  • Previous tag: {previous_tag.display_name}")
        
        # Ensure output folder exists
        if not self.output_folder.exists():
            logger.info(f"  • Creating output folder: {self.output_folder}")
            self.output_folder.mkdir(parents=True, exist_ok=True)

        # Prepare build directories
        if not self.build_dir.exists():
            logger.info(f"  • Creating build directory: {self.build_dir}")
            self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup checkout directories
        logger.info(f"  • Setting up checkout directories")
        checkout_dirs = self._prepare_checkout_directories(current, previous_commit, previous_tag)

        try:
            # Build the current version first
            logger.info(f"  • Building current version")
            self._build_current_version(current, checkout_dirs["current"])
        except Exception as e:
            logger.error(f"  • Failed to build current version: {repr(e)}")

        try:

            # Generate and build diff files
            logger.info(f"  • Generating and building diff files")
            self._generate_and_build_diffs(current, previous_commit, previous_tag, checkout_dirs)
        except Exception as e:
            logger.error(f"  • Failed to generate and build diffs: {repr(e)}")
        
        # Save metadata
        logger.info(f"  • Saving metadata")
        self._save_metadata(current, previous_commit, previous_tag)
        
        logger.info("STEP 12: All operations completed successfully")
    
    def _build_current_version(self, current: GitRevision, current_dir: Path) -> None:
        """
        Build the current version of the LaTeX document.
        
        Args:
            current: Current Git revision
            current_dir: Path to the directory for the current revision
        """
        logger.info(f"  • Building current version: {current.display_name}")
        original_dir = Path.cwd()
        logger.info(f"    - Current working directory: {original_dir}")

        # Generate revision file
        revision_file_path = current_dir / self.config.revision_path
        logger.info(f"    - Generating revision file at: {revision_file_path}")
        self.git_repo.generate_revision_file(
            current, 
            revision_file_path,
        )

        logger.info(f"    - Generating revision file at: {revision_file_path}")
        self.git_repo.generate_revision_file(
            current, 
            Path(self.config.revision_path),
        )

        # Build document
        logger.info(f"    - Building LaTeX document")
        self.latex_processor.build_document(
            self.config.tex_file, 
            original_dir, 
            self.output_folder, 
            f"{current.display_name}.pdf"
        )
        logger.info(f"    - Current version build completed")
    
    def _prepare_checkout_directories(self, 
                                     current: GitRevision, 
                                     previous_commit: GitRevision, 
                                     previous_tag: GitRevision) -> Dict[str, Path]:
        """
        Prepare directories for checking out different Git revisions.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
            
        Returns:
            Dictionary mapping revision names to checkout directories
        """
        # Setup checkout directories
        current_commit_dir = self.build_dir / "current_commit"
        previous_commit_dir = self.build_dir / "previous_commit"
        previous_tag_dir = self.build_dir / "previous_tag"
        
        logger.info(f"    - Current commit directory: {current_commit_dir}")
        logger.info(f"    - Previous commit directory: {previous_commit_dir}")
        logger.info(f"    - Previous tag directory: {previous_tag_dir}")
        
        # Checkout all needed revisions
        logger.info(f"    - Checking out current revision: {current.display_name}")
        self.git_repo.checkout_revision(current, current_commit_dir)
        
        logger.info(f"    - Checking out previous commit: {previous_commit.display_name}")
        self.git_repo.checkout_revision(previous_commit, previous_commit_dir)
        
        logger.info(f"    - Checking out previous tag: {previous_tag.display_name}")
        self.git_repo.checkout_revision(previous_tag, previous_tag_dir)
        
        logger.info(f"    - All revisions checked out successfully")
        
        return {
            "current": current_commit_dir,
            "previous_commit": previous_commit_dir,
            "previous_tag": previous_tag_dir
        }
    
    def _generate_and_build_diffs(self, 
                                 current: GitRevision, 
                                 previous_commit: GitRevision, 
                                 previous_tag: GitRevision,
                                 checkout_dirs: Dict[str, Path]) -> None:
        """
        Generate and build diff files.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
            checkout_dirs: Dictionary mapping revision names to checkout directories
        """
        # Generate diff file names
        tag_diff_name = f"diff-{previous_tag.short_hash}-{current.short_hash}.tex"
        commit_diff_name = f"diff-{previous_commit.short_hash}-{current.short_hash}.tex"
        
        logger.info(f"    - Tag diff filename: {tag_diff_name}")
        logger.info(f"    - Commit diff filename: {commit_diff_name}")

        # Generate tag diff
        logger.info(f"    - Generating diff since last tag")
        self.latex_processor.generate_diff(
            checkout_dirs["previous_tag"] / self.config.tex_file,
            checkout_dirs["current"] / self.config.tex_file,
            checkout_dirs["previous_tag"] / tag_diff_name
        )
        
        # Generate commit diff
        logger.info(f"    - Generating diff since last commit")
        self.latex_processor.generate_diff(
            checkout_dirs["previous_commit"] / self.config.tex_file,
            checkout_dirs["current"] / self.config.tex_file,
            checkout_dirs["previous_commit"] / commit_diff_name
        )
        
        # Build tag diff document
        logger.info(f"    - Building tag diff document")
        self.latex_processor.build_document(
            tag_diff_name, 
            checkout_dirs["previous_tag"], 
            self.output_folder / "diff", 
            f"since-last-tag-{previous_tag.display_name}.pdf"
        )
        
        # Build commit diff document
        logger.info(f"    - Building commit diff document")
        self.latex_processor.build_document(
            commit_diff_name, 
            checkout_dirs["previous_commit"], 
            self.output_folder / "diff", 
            f"since-last-commit-{previous_commit.short_hash}.pdf"
        )
        
        logger.info(f"    - All diff documents built successfully")
    
    def _save_metadata(self, 
                      current: GitRevision, 
                      previous_commit: GitRevision, 
                      previous_tag: GitRevision) -> None:
        """
        Save metadata about the diff generation.
        
        Args:
            current: Current Git revision
            previous_commit: Previous commit revision
            previous_tag: Previous tag revision
        """
        metadata = {
            "current_commit": current.short_hash,
            "current_display_name": current.display_name,
            "previous_commit": previous_commit.short_hash,
            "previous_commit_display_name": previous_commit.display_name,
            "previous_tag": previous_tag.tag_name or previous_tag.short_hash,
            "previous_tag_display_name": previous_tag.display_name,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        logger.info(f"    - Creating metadata:")
        for key, value in metadata.items():
            logger.info(f"      • {key}: {value}")
        
        metadata_file = self.output_folder / "metadata.json"
        logger.info(f"    - Writing metadata to: {metadata_file}")
        
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)
        
        logger.info(f"    - Metadata saved successfully")


class LatexDiffTool:
    """Main application class for LaTeX diff tool."""
    
    def __init__(self, config: Config):
        """
        Initialize LatexDiffTool.
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # Set log level based on verbosity
        if config.verbose:
            logger.setLevel(logging.DEBUG)
            logger.info("Verbose logging enabled")
        
        # Initialize components
        logger.info("Initializing LaTeX Diff Tool")
        logger.info(f"Configuration:")
        logger.info(f"  • LaTeX file: {config.tex_file}")
        logger.info(f"  • Revision path: {config.revision_path}")
        logger.info(f"  • Output folder: {config.output_folder}")
        logger.info(f"  • Build directory: {config.build_dir}")
        logger.info(f"  • Verbose mode: {config.verbose}")
        
        self.git_repo = GitRepository()
        self.latex_processor = LaTeXProcessor()
        self.diff_generator = DiffGenerator(
            self.git_repo, 
            self.latex_processor,
            config
        )
    
    def run(self) -> int:
        """
        Execute the main workflow.
        
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        start_time = time.time()
        logger.info("Starting LaTeX Diff Tool execution")
        
        try:
            # Get Git revisions
            current = self.git_repo.get_current_revision()
            previous_commit = self.git_repo.get_previous_commit()
            previous_tag = self.git_repo.get_previous_tag()
            
            if not previous_commit:
                logger.error("No previous commit found, cannot generate diff")
                return 1
            
            # Generate diffs
            logger.info("Starting diff generation process")
            self.diff_generator.generate_diffs(
                current,
                previous_commit,
                previous_tag
            )
            
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"Process completed successfully in {duration:.2f} seconds")
            
            return 0
        except Exception as e:
            logger.error(f"An unexpected error occurred: {repr(e)}")
            return 1


def parse_arguments() -> Config:
    """
    Parse command line arguments.
    
    Returns:
        Config object with parsed arguments
    """
    logger.info("Parsing command line arguments")
    
    parser = argparse.ArgumentParser(
        description="LaTeX build and diff tool for Git repositories",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "-t", "--tex-file", 
        default="main.tex", 
        help="Main LaTeX file to compile"
    )
    
    parser.add_argument(
        "-r", "--revision-path", 
        default="miscellaneous/revision.tex", 
        help="Path for revision.tex"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "-o", "--output-folder",
        default="output",
        help="Folder for output files"
    )
    
    parser.add_argument(
        "-b", "--build-dir",
        default="build",
        help="Directory for build files"
    )
    
    args = parser.parse_args()
    logger.info(f"Arguments parsed: {vars(args)}")
    
    return Config(
        tex_file=args.tex_file,
        revision_path=args.revision_path,
        verbose=args.verbose,
        output_folder=Path(args.output_folder),
        build_dir=Path(args.build_dir)
    )


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("LaTeX Diff Tool starting")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    config = parse_arguments()
    tool = LatexDiffTool(config)
    
    logger.info("Running LaTeX Diff Tool")
    result = tool.run()
    
    if result == 0:
        logger.info("LaTeX Diff Tool completed successfully")
    else:
        logger.error("LaTeX Diff Tool failed")
    
    return result


if __name__ == "__main__":
    logger.info("Script execution started")
    sys.exit(main())