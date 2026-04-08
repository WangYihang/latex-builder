"""LaTeX compilation."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from latex_builder import log, shell
from latex_builder.config import Compiler

logger = log.get(__name__)


def build(
    tex_file: str,
    *,
    working_dir: Path,
    output_dir: Path,
    output_name: str = "output.pdf",
    compiler: Compiler = Compiler.XELATEX,
    timeout: int = 300,
) -> Path:
    """Compile a LaTeX document and copy the PDF to *output_dir*.

    Returns the path of the produced PDF.

    Raises:
        RuntimeError: if compilation fails or the PDF is not produced.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = Path(tex_file).stem
    cc = compiler.value

    # Three-pass compilation: compiler → bibtex → compiler → compiler
    logger.info("compiling", compiler=cc, file=tex_file)
    shell.run_latex([cc, "-shell-escape", tex_file], cwd=working_dir, timeout=timeout)

    # bibtex may fail if there are no citations — that's fine
    try:
        shell.run_latex(["bibtex", basename], cwd=working_dir, timeout=timeout)
    except RuntimeError:
        logger.debug("bibtex skipped (no citations or .bib)")

    shell.run_latex([cc, "-shell-escape", tex_file], cwd=working_dir, timeout=timeout)
    shell.run_latex([cc, "-shell-escape", tex_file], cwd=working_dir, timeout=timeout)

    pdf = working_dir / f"{basename}.pdf"
    if not pdf.exists():
        raise RuntimeError(f"PDF not produced: {pdf}")

    dest = output_dir / output_name
    shutil.copy2(pdf, dest)
    logger.info("pdf ready", path=str(dest))
    return dest


def latexdiff(old: Path, new: Path, out: Path) -> Path:
    """Run latexdiff --flatten and write the result to *out*.

    Returns *out* on success.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["latexdiff", "--flatten", str(old), str(new)],
        capture_output=True, text=True, check=True,
    )
    out.write_text(result.stdout, encoding="utf-8")
    logger.info("diff generated", path=str(out))
    return out
