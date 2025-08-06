# LaTeX Builder

A Python tool for building LaTeX documents with Git version management and automatic diff generation.

## Features

- **Git Integration**: Automatic detection of current commit, branch, and tag information
- **LaTeX Compilation**: Complete compilation workflow using XeLaTeX and BibTeX
- **Diff Generation**: Create visual differences between Git versions using latexdiff
- **Version Management**: Generate version information files for LaTeX documents
- **Clear Logging**: Beautiful command-line interface with clear progress indicators
- **GoReleaser-like Versioning**: Smart version naming based on Git tags and working tree status

## Version Naming Logic

The tool uses GoReleaser-like version naming:

- **Tag commits**: `{tag}-{commit}` (e.g., `v1.2.3-a1b2c3d`)
- **Non-tag commits**: `{next_version}-snapshot-{commit}` (e.g., `v1.2.4-snapshot-a1b2c3d`)
- **Dirty working tree**: `{version}-dirty-{commit}` (e.g., `v1.2.4-dirty-a1b2c3d`)

Where `{next_version}` is the patch-bumped version of the latest semantic version tag.

## Usage

### Command Line

```bash
# Basic usage (in Git repository containing main.tex)
pipx run latex-builder

# Specify LaTeX file
pipx run latex-builder -t document.tex

# Specify output directory
pipx run latex-builder -o build_output

# Enable verbose output
pipx run latex-builder -v

# Full options
pipx run latex-builder -t main.tex -r misc/revision.tex -o output -b build -v
```

### Generate Only revision.tex

```bash
# Generate revision.tex only (no build or diff)
pipx run latex-builder revision

# Specify output path for revision.tex
pipx run latex-builder revision --revision-file misc/revision.tex
```

### Python API

```python
from latex_builder import Config, LatexDiffTool
from pathlib import Path

# Create configuration
config = Config(
    tex_file="main.tex",
    revision_path="misc/revision.tex",
    output_folder=Path("output"),
    build_dir=Path("build"),
    verbose=True
)

# Run tool
tool = LatexDiffTool(config)
exit_code = tool.run()
```

## Package Structure

```
latex_builder/
├── cli/                    # Command line interface
│   ├── main.py            # Main application class
│   └── parser.py          # Command line argument parsing
├── config/                # Configuration management
│   └── settings.py        # Configuration data classes
├── diff/                  # Diff generation
│   └── generator.py       # LaTeX diff operations
├── git/                   # Git operations
│   ├── repository.py      # Git repository handling
│   └── revision.py        # Git version data structures
├── latex/                 # LaTeX processing
│   └── processor.py       # LaTeX compilation
└── utils/                 # Shared utilities
    ├── command.py         # Command execution
    └── logging.py         # Logging setup
```

## Configuration Options

- `tex_file`: Main LaTeX file to compile (default: "main.tex")
- `revision_path`: Path to revision.tex file (default: "variables/revision.tex")
- `verbose`: Enable debug logging (default: False)
- `output_folder`: Output files directory (default: "output")
- `build_dir`: Temporary build files directory (default: "build")

## Output Files

The tool generates the following output files:

- **Current Version PDF**: `{version-name}.pdf`
- **Diff PDFs**: 
  - `diff/since-last-commit-{hash}.pdf`
  - `diff/since-last-tag-{tag}.pdf`
- **Metadata**: `metadata.json` containing version information
- **Version File**: `revision.tex` containing version macros for LaTeX

## Requirements

- Python 3.11+
- Git repository
- LaTeX installation including:
  - XeLaTeX
  - BibTeX
  - latexdiff

## Example

```bash
# In a Git repository containing LaTeX project
cd my-latex-project

# Install package
uv pip install -e /path/to/latex-builder

# Build current version and generate diffs
uv run latex-builder -v
```

This will:
1. Analyze current Git state
2. Generate version information files
3. Compile current version PDF
4. Generate diff documents with previous commit and previous tag
5. Output all files to `output/` directory

## Architecture

The package uses a modular architecture with clear separation of concerns:

- **CLI Layer**: Handles command line interaction
- **Core Logic**: Git operations, LaTeX processing, diff generation
- **Configuration**: Centralized settings management
- **Utilities**: Shared functionality for logging and command execution

Each module can be tested independently, following Python best practices.
