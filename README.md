# LaTeX Builder

Build LaTeX documents with Git-based versioning and automatic diff generation.

## Features

- **Git integration** — automatic version naming based on tags, commits, and dirty state
- **LaTeX compilation** — xelatex / pdflatex / lualatex with bibtex
- **Diff generation** — visual diffs between Git versions via latexdiff
- **GitHub Action** — use directly in CI/CD workflows
- **CLI tool** — installable via pip / uvx for local use

## Use as a GitHub Action

```yaml
- uses: wangyihang/latex-builder@v1
  with:
    tex-file: main.tex
```

### Full example workflow

```yaml
name: Build LaTeX

on:
  push:
    branches: [main]
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # needed for diff against previous tags

      - uses: wangyihang/latex-builder@v1
        id: latex
        with:
          tex-file: main.tex
          compiler: xelatex
          output-dir: output

      - uses: actions/upload-artifact@v4
        with:
          name: latex-output
          path: |
            ${{ steps.latex.outputs.pdf-path }}
            ${{ steps.latex.outputs.diff-pdf-path }}
            ${{ steps.latex.outputs.metadata-path }}
```

### Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `tex-file` | `main.tex` | Main .tex file to compile |
| `compiler` | `xelatex` | LaTeX compiler (`xelatex`, `pdflatex`, `lualatex`) |
| `compare-with` | *(auto)* | Git tag or commit to compare against |
| `output-dir` | `output` | Directory for output files |
| `timeout` | `300` | Per-command timeout in seconds |
| `revision-file` | `variables/revision.tex` | Path for generated revision.tex |
| `skip-diff` | `false` | Build current version only |
| `diff-only` | `false` | Generate diff .tex without building PDFs |
| `verbose` | `false` | Enable debug logging |
| `texlive-packages` | *(empty)* | Extra TeXLive packages to install (space-separated) |

> The Action uses a **composite** runner (not Docker), so TeXLive is installed
> on the GitHub-hosted runner and **cached automatically** between runs.
> First run takes ~2 minutes; subsequent runs with cache hit take ~10 seconds.

### Outputs

| Output | Description |
|--------|-------------|
| `version-name` | Generated version string (e.g. `v1.2.3-abc1234-20240101120000`) |
| `pdf-path` | Path to the current-version PDF |
| `diff-pdf-path` | Path to the diff PDF |
| `diff-tex-path` | Path to the diff .tex source |
| `metadata-path` | Path to `metadata.json` |

## Use as a CLI tool

### Install

```bash
pip install latex-builder
# or
uvx latex-builder --help
```

### Commands

```bash
# Build and generate diffs (default)
latex-builder build

# Specify options
latex-builder build -f thesis.tex -c pdflatex -o dist --compare-with v1.0.0

# Build without diff
latex-builder build --skip-diff

# Generate diff .tex only (no PDF)
latex-builder build --diff-only

# Generate only revision.tex
latex-builder revision
```

### Python API

```python
from pathlib import Path
from latex_builder import Config, Compiler, GitRepo
from latex_builder.diff import build_and_diff

repo = GitRepo(Path("."))
current = repo.current_revision()
compare = repo.auto_compare_target()

cfg = Config(compiler=Compiler.XELATEX, output_dir=Path("output"))
build_and_diff(repo, current, compare, cfg)
```

## Version naming

Follows GoReleaser-style naming:

| Scenario | Format | Example |
|----------|--------|---------|
| Tagged commit | `{tag}-{hash}` | `v1.2.3-abc1234` |
| Untagged commit | `{next}-snapshot-{hash}` | `v1.2.4-snapshot-abc1234` |
| Dirty tree | adds `-dirty` | `v1.2.4-snapshot-abc1234-dirty` |

## Output files

- `{version}.pdf` — current version PDF (e.g. `v1.2.4-snapshot-abc1234.pdf`)
- `diff-{old_hash}-vs-{new_hash}.tex` — diff LaTeX source
- `diff-{old_hash}-vs-{new_hash}.pdf` — diff PDF
- `metadata.json` — build metadata (includes timestamps, full version names)
- `revision.tex` — LaTeX macros (`\GitCommit`, `\GitTag`, `\GitBranch`, `\GitRevision`, `\CompiledDate`)

## Requirements

- Python 3.11+
- Git
- LaTeX (xelatex/pdflatex/lualatex + bibtex + latexdiff)

All dependencies are bundled in the Docker image / GitHub Action.

## Project structure

```
latex_builder/
├── cli.py         # click-based CLI
├── config.py      # Config dataclass + Compiler enum
├── revision.py    # Frozen Revision dataclass
├── git.py         # Git operations
├── compiler.py    # LaTeX compilation
├── diff.py        # Diff orchestration
├── shell.py       # Subprocess runner
└── log.py         # Structured logging
```
