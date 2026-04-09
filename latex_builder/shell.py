"""Subprocess execution utilities."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from latex_builder import log

logger = log.get(__name__)

# LaTeX compilers that accept -interaction flags
_LATEX_COMPILERS = {"xelatex", "pdflatex", "lualatex"}

_INTERACTION_FLAGS = frozenset({
    "-interaction=nonstopmode",
    "-interaction=batchmode",
    "-interaction=scrollmode",
})


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 300,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the result.

    Raises:
        RuntimeError: on non-zero exit (when *check* is True) or timeout.
    """
    cmd_str = " ".join(cmd)
    logger.debug("exec", cmd=cmd_str, cwd=str(cwd))

    env = {**os.environ, "LATEX_INTERACTION": "batchmode"}

    try:
        result = subprocess.run(
            cmd, cwd=cwd, env=env, timeout=timeout, capture_output=True, text=True,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd_str}")
    except OSError as exc:
        raise RuntimeError(f"Command failed to start: {cmd_str}") from exc

    if check and result.returncode != 0:
        stderr_preview = (result.stderr or "").strip()
        stdout_tail = (result.stdout or "").strip()
        # LaTeX compilers write errors to stdout, so include both streams
        parts = [f"Command failed (exit {result.returncode}): {cmd_str}"]
        if stdout_tail:
            parts.append(f"stdout (last 3000 chars):\n{stdout_tail[-3000:]}")
        if stderr_preview:
            parts.append(f"stderr (first 500 chars):\n{stderr_preview[:500]}")
        raise RuntimeError("\n".join(parts))
    return result


def run_latex(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 300,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a LaTeX command, auto-injecting -interaction=nonstopmode."""
    cmd = list(cmd)  # copy
    if cmd and cmd[0] in _LATEX_COMPILERS:
        if not any(flag in cmd for flag in _INTERACTION_FLAGS):
            cmd.insert(1, "-interaction=nonstopmode")
    return run(cmd, cwd=cwd, timeout=timeout, check=check)
