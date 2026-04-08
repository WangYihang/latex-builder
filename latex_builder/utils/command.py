"""Command execution utilities."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional

from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


def run_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> None:
    """Execute shell command.

    Args:
        cmd: Command to run as list of strings
        cwd: Working directory for command execution
        timeout: Timeout in seconds (default: 5 minutes)

    Raises:
        RuntimeError: If command execution fails or times out
    """
    cmd_str = " ".join(cmd)
    logger.debug("Executing command", command=cmd_str, working_dir=str(cwd), timeout=timeout)

    try:
        # 使用非交互式模式，避免等待用户输入
        env = dict(os.environ)
        env.update({
            'LATEX_INTERACTION': 'batchmode',
            'TEXMFVAR': '/dev/null'
        })
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.warning(
                "Command exited with non-zero code",
                command=cmd_str,
                returncode=result.returncode,
                stderr=result.stderr[:500] if result.stderr else "",
            )
            raise RuntimeError(
                f"Command failed (exit code {result.returncode}): {cmd_str}\n{result.stderr[:500] if result.stderr else ''}"
            )
    except subprocess.TimeoutExpired:
        logger.error("Command timed out", command=cmd_str, timeout=timeout)
        raise RuntimeError(f"Command timed out after {timeout} seconds: {cmd_str}")
    except Exception as e:
        logger.error("Command execution error", command=cmd_str, error=str(e))
        raise RuntimeError(f"Command failed: {cmd_str}") from e


def run_latex_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> None:
    """Execute LaTeX command with non-interactive mode.

    Args:
        cmd: LaTeX command to run as list of strings
        cwd: Working directory for command execution
        timeout: Timeout in seconds (default: 5 minutes)

    Raises:
        RuntimeError: If command execution fails or times out
    """
    # 为LaTeX命令添加非交互式参数
    latex_cmd = cmd.copy()
    
    # 检查是否已经包含非交互式参数
    interactive_flags = ['-interaction=nonstopmode', '-interaction=batchmode', '-interaction=scrollmode']
    has_interactive_flag = any(flag in ' '.join(latex_cmd) for flag in interactive_flags)
    
    if not has_interactive_flag:
        # 在命令中添加非交互式模式
        if latex_cmd[0] in ['xelatex', 'pdflatex', 'lualatex']:
            latex_cmd.insert(1, '-interaction=nonstopmode')
    
    return run_command(latex_cmd, cwd, timeout)
