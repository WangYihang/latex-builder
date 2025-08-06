"""Command execution utilities."""

import subprocess
from pathlib import Path
from typing import List, Optional

from latex_builder.utils.logging import get_logger

logger = get_logger(__name__)


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> str:
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
