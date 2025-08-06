"""Command execution utilities."""

import subprocess
from pathlib import Path
from typing import List, Optional

from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> str:
    """Execute shell command and return output.

    Args:
        cmd: Command to run as list of strings
        cwd: Working directory for command execution

    Returns:
        Command output as string

    Raises:
        RuntimeError: If command execution fails
    """
    cmd_str = " ".join(cmd)
    logger.debug("Executing command", command=cmd_str, working_dir=str(cwd))

    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stdout_lines = []

        while True:
            stdout_line = process.stdout.readline() if process.stdout else ""
            stderr_line = process.stderr.readline() if process.stderr else ""

            if stdout_line:
                logger.debug(
                    "Command output", stream="stdout", line=stdout_line.rstrip()
                )
                stdout_lines.append(stdout_line)

            if stderr_line:
                logger.debug(
                    "Command output", stream="stderr", line=stderr_line.rstrip()
                )

            if not stdout_line and not stderr_line and process.poll() is not None:
                break

        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            logger.debug(
                "Command output", stream="stdout", line=remaining_stdout.rstrip()
            )
            stdout_lines.append(remaining_stdout)
        if remaining_stderr:
            logger.debug(
                "Command output", stream="stderr", line=remaining_stderr.rstrip()
            )

        if process.returncode != 0:
            logger.error(
                "Command failed", command=cmd_str, exit_code=process.returncode
            )
            raise RuntimeError(
                f"Command failed with exit code {process.returncode}: {cmd_str}"
            )

        return "".join(stdout_lines).strip()
    except Exception as e:
        logger.error("Command execution error", command=cmd_str, error=str(e))
        raise RuntimeError(f"Command failed: {cmd_str}") from e
