"""Command-line interface using click."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from latex_builder import log
from latex_builder.config import Compiler, Config
from latex_builder.diff import build_and_diff, build_only, diff_only
from latex_builder.git import GitRepo

logger = log.get(__name__)


class CompilerType(click.ParamType):
    name = "compiler"

    def convert(self, value, param, ctx):
        try:
            return Compiler(value)
        except ValueError:
            self.fail(f"Unknown compiler '{value}'. Choose from: xelatex, pdflatex, lualatex", param, ctx)


COMPILER = CompilerType()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """LaTeX build & diff tool for Git repositories."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(build)


@main.command()
@click.argument("repo", default=".", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("-f", "--file", "tex_file", default="main.tex", show_default=True, help="Main .tex file.")
@click.option("-c", "--compiler", "compiler_", default="xelatex", type=COMPILER, show_default=True, help="LaTeX compiler.")
@click.option("--compare-with", default=None, help="Tag or commit to compare against.")
@click.option("-o", "--output", "output_dir", default="output", show_default=True, help="Output directory.")
@click.option("-t", "--timeout", default=300, show_default=True, help="Per-command timeout (seconds).")
@click.option("--revision-file", default="variables/revision.tex", show_default=True, help="Path for revision.tex.")
@click.option("--skip-diff", is_flag=True, help="Build current version only.")
@click.option("--diff-only", "diff_only_", is_flag=True, help="Generate diff .tex without building PDFs.")
@click.option("-v", "--verbose", is_flag=True, help="Debug logging.")
@click.option("-q", "--quiet", is_flag=True, help="Errors only.")
def build(
    repo: str,
    tex_file: str,
    compiler_: Compiler,
    compare_with: str | None,
    output_dir: str,
    timeout: int,
    revision_file: str,
    skip_diff: bool,
    diff_only_: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """Build the LaTeX project and generate diffs."""
    log.setup(verbose=verbose, quiet=quiet)
    cfg = Config(
        repo_path=Path(repo),
        tex_file=tex_file,
        compiler=compiler_,
        compare_with=compare_with,
        output_dir=Path(output_dir),
        timeout=timeout,
        revision_file=revision_file,
        skip_diff=skip_diff,
        diff_only=diff_only_,
        verbose=verbose,
        quiet=quiet,
    )
    sys.exit(_run_build(cfg))


@main.command()
@click.argument("repo", default=".", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--revision-file", default="variables/revision.tex", show_default=True, help="Output path.")
@click.option("-v", "--verbose", is_flag=True)
@click.option("-q", "--quiet", is_flag=True)
def revision(repo: str, revision_file: str, verbose: bool, quiet: bool) -> None:
    """Generate only revision.tex (no build)."""
    log.setup(verbose=verbose, quiet=quiet)
    try:
        git = GitRepo(Path(repo))
        rev = git.current_revision()
        git.write_revision_tex(rev, Path(revision_file))
        logger.info("revision.tex written", path=revision_file)
    except Exception as exc:
        logger.error("failed", error=str(exc))
        sys.exit(1)


# ------------------------------------------------------------------

def _run_build(cfg: Config) -> int:
    try:
        git = GitRepo(cfg.repo_path)
        tex_path = cfg.repo_path / cfg.tex_file
        if not tex_path.exists():
            logger.error("tex file not found", path=str(tex_path))
            return 1

        current = git.current_revision()

        # Resolve comparison target
        if cfg.compare_with:
            compare = git.revision_for_ref(cfg.compare_with)
            if compare is None:
                logger.error("compare target not found", ref=cfg.compare_with)
                return 1
        else:
            compare = git.auto_compare_target()
            if compare is None:
                logger.error("no previous commit or tag to compare against")
                return 1

        if cfg.diff_only:
            diff_only(git, current, compare, cfg)
        elif cfg.skip_diff:
            build_only(git, current, cfg)
        else:
            build_and_diff(git, current, compare, cfg)

        logger.info("done")
        return 0
    except Exception as exc:
        logger.error("build failed", error=str(exc))
        return 1
