"""Command execution utilities."""

import os
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


def run_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> str:
    """Execute shell command and return output.

    Args:
        cmd: Command to run as list of strings
        cwd: Working directory for command execution
        timeout: Timeout in seconds (default: 5 minutes)

    Returns:
        Command output as string

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
        
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )

        stdout_lines = []
        stderr_lines = []
        start_time = time.time()

        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                logger.error("Command timed out", command=cmd_str, timeout=timeout)
                process.terminate()
                try:
                    process.wait(timeout=10)  # 给进程10秒来优雅退出
                except subprocess.TimeoutExpired:
                    process.kill()  # 强制终止
                raise RuntimeError(f"Command timed out after {timeout} seconds: {cmd_str}")

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
                stderr_lines.append(stderr_line)

            # 检查进程是否结束
            if not stdout_line and not stderr_line and process.poll() is not None:
                break

            # 短暂休眠避免CPU占用过高
            time.sleep(0.1)

        # 获取剩余输出
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
            stderr_lines.append(remaining_stderr)

        # 检查退出码
        if process.returncode != 0:
            stderr_output = "".join(stderr_lines).strip()
            logger.error(
                "Command failed", 
                command=cmd_str, 
                exit_code=process.returncode,
                stderr=stderr_output
            )
            
            # 提供更详细的错误信息
            error_msg = f"Command failed with exit code {process.returncode}: {cmd_str}"
            if stderr_output:
                error_msg += f"\nError output: {stderr_output}"
            
            raise RuntimeError(error_msg)

        return "".join(stdout_lines).strip()
        
    except subprocess.TimeoutExpired:
        logger.error("Command timed out", command=cmd_str, timeout=timeout)
        raise RuntimeError(f"Command timed out after {timeout} seconds: {cmd_str}")
    except Exception as e:
        logger.error("Command execution error", command=cmd_str, error=str(e))
        raise RuntimeError(f"Command failed: {cmd_str}") from e


def run_latex_command(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> str:
    """Execute LaTeX command with non-interactive mode.

    Args:
        cmd: LaTeX command to run as list of strings
        cwd: Working directory for command execution
        timeout: Timeout in seconds (default: 5 minutes)

    Returns:
        Command output as string

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
