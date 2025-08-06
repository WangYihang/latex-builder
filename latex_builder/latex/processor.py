"""LaTeX document processing operations."""

import shutil
import time
from pathlib import Path
from typing import Optional

from latex_builder.utils.logging import get_logger
from latex_builder.utils.command import run_command

logger = get_logger(__name__)


class LaTeXProcessor:
    """Handles LaTeX document processing operations."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize LaTeXProcessor.
        
        Args:
            base_dir: Base directory for operations, defaults to current directory
        """
        self.base_dir = base_dir or Path.cwd()
        logger.info("LaTeX processor initialized", base_dir=str(self.base_dir))
    
    def build_document(self, 
                      tex_file: str, 
                      working_dir: Optional[Path] = None, 
                      output_folder: Optional[Path] = None, 
                      output_filename: str = "main.pdf",
                      compiler: str = "xelatex") -> None:
        """Build LaTeX document using specified compiler and bibtex.
        
        Args:
            tex_file: Name of .tex file to compile
            working_dir: Directory to run commands in (defaults to self.base_dir)
            output_folder: Directory for output files
            output_filename: Name of output file (without extension)
            compiler: LaTeX compiler to use (xelatex, pdflatex, lualatex)
            
        Raises:
            RuntimeError: If build fails
        """
        start_time = time.time()
        cwd = working_dir or self.base_dir
        output_folder = output_folder or self.base_dir
        
        logger.info("Building LaTeX document", 
                   tex_file=tex_file,
                   working_dir=str(cwd),
                   output_folder=str(output_folder),
                   output_filename=output_filename)
        
        try:
            logger.info("Starting LaTeX compilation process")
            self._run_latex_commands(tex_file, cwd, compiler)
            
            basename = Path(tex_file).stem
            pdf_file = cwd / f"{basename}.pdf"
            
            if pdf_file.exists():
                if not output_folder.exists():
                    logger.info("Creating output folder", path=str(output_folder))
                    output_folder.mkdir(parents=True, exist_ok=True)
                
                output_path = output_folder / output_filename
                logger.info("Copying PDF to output", 
                           source=str(pdf_file), 
                           destination=str(output_path))
                shutil.copy(pdf_file, output_path)
                
                end_time = time.time()
                duration = end_time - start_time
                logger.info("LaTeX build completed", 
                           output_path=str(output_path),
                           duration=f"{duration:.2f}s")
            else:
                logger.error("PDF file not found", expected_path=str(pdf_file))
                raise RuntimeError(f"PDF file not found: {pdf_file}")
        except Exception as e:
            logger.error("LaTeX build failed", error=str(e))
            raise RuntimeError(f"LaTeX build failed: {repr(e)}")
    
    def _run_latex_commands(self, tex_file: str, cwd: Path, compiler: str = "xelatex") -> None:
        """Run LaTeX commands to compile document.
        
        Args:
            tex_file: Name of .tex file to compile
            cwd: Directory to run commands in
            compiler: LaTeX compiler to use (xelatex, pdflatex, lualatex)
            
        Raises:
            RuntimeError: If any command fails
        """
        basename = Path(tex_file).stem
        
        # Validate compiler
        valid_compilers = ["xelatex", "pdflatex", "lualatex"]
        if compiler not in valid_compilers:
            raise RuntimeError(f"Unsupported compiler: {compiler}. Valid options: {valid_compilers}")
        
        logger.info(f"Running {compiler} first pass")
        cmd_start = time.time()
        run_command([compiler, "-shell-escape", tex_file], cwd)
        logger.debug(f"{compiler} first pass completed", duration=f"{time.time() - cmd_start:.2f}s")
        
        logger.info("Running bibtex")
        cmd_start = time.time()
        run_command(["bibtex", basename], cwd)
        logger.debug("bibtex completed", duration=f"{time.time() - cmd_start:.2f}s")
        
        logger.info(f"Running {compiler} second pass")
        cmd_start = time.time()
        run_command([compiler, "-shell-escape", tex_file], cwd)
        logger.debug(f"{compiler} second pass completed", duration=f"{time.time() - cmd_start:.2f}s")
        
        logger.info(f"Running {compiler} final pass")
        cmd_start = time.time()
        run_command([compiler, "-shell-escape", tex_file], cwd)
        logger.debug(f"{compiler} final pass completed", duration=f"{time.time() - cmd_start:.2f}s")
        
        logger.info("LaTeX compilation sequence completed", tex_file=tex_file, compiler=compiler)
    
    def generate_diff(self, 
                     original_file: Path, 
                     modified_file: Path, 
                     output_file: Path) -> None:
        """Generate LaTeX diff between two files.
        
        Args:
            original_file: Path to original .tex file
            modified_file: Path to modified .tex file
            output_file: Path to save diff .tex file
            
        Raises:
            RuntimeError: If diff generation fails
        """
        start_time = time.time()
        
        logger.info("Generating LaTeX diff",
                   original_file=str(original_file),
                   modified_file=str(modified_file),
                   output_file=str(output_file))
        
        try:
            if not output_file.parent.exists():
                logger.info("Creating output directory", path=str(output_file.parent))
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info("Running latexdiff with flatten option")
            result = run_command([
                "latexdiff", 
                "--flatten", 
                str(original_file), 
                str(modified_file)
            ])
            
            logger.info("Writing diff output", output_file=str(output_file))
            with open(output_file, "w") as f:
                f.write(result)
            
            end_time = time.time()
            duration = end_time - start_time    
            logger.info("Diff generation completed", 
                       output_file=str(output_file),
                       duration=f"{duration:.2f}s")
        except Exception as e:
            logger.error("Failed to generate diff", error=str(e))
            raise RuntimeError(f"Failed to generate diff: {repr(e)}")
