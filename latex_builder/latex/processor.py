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
        run_command(["xelatex", "-shell-escape", tex_file], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • [2/4] Running bibtex")
        cmd_start = time.time()
        run_command(["bibtex", basename], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • [3/4] Running second xelatex pass")
        cmd_start = time.time()
        run_command(["xelatex", "-shell-escape", tex_file], cwd)
        logger.info(f"  •      Completed in {time.time() - cmd_start:.2f} seconds")
        
        logger.info(f"  • [4/4] Running final xelatex pass")
        cmd_start = time.time()
        run_command(["xelatex", "-shell-escape", tex_file], cwd)
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
            result = run_command([
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
