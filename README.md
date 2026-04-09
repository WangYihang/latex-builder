# LaTeX Builder

Build LaTeX documents with Git-based versioning and automatic diff generation.

## GitHub Action

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0

  - name: Install TeX Live
    uses: zauguin/install-texlive@v4
    with:
      packages: >
        scheme-basic
        xetex
        latexmk
        bibtex
        biber
        latexdiff
        collection-fontsrecommended
        collection-latexextra

  - uses: wangyihang/latex-builder@v1
    id: latex
    with:
      tex-file: main.tex

  - uses: actions/upload-artifact@v4
    with:
      name: pdf
      path: |
        ${{ steps.latex.outputs.pdf-path }}
        ${{ steps.latex.outputs.diff-pdf-path }}
```

### Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `tex-file` | `main.tex` | Main .tex file |
| `compiler` | `xelatex` | `xelatex` / `pdflatex` / `lualatex` |
| `compare-with` | *(auto)* | Tag or commit to diff against |
| `output-dir` | `output` | Output directory |
| `timeout` | `300` | Per-command timeout (seconds) |
| `skip-diff` | `false` | Build only, no diff |
| `diff-only` | `false` | Diff only, no PDF build |

### Outputs

| Output | Description |
|--------|-------------|
| `version-name` | e.g. `v1.2.3-abc1234` |
| `pdf-path` | Current version PDF |
| `diff-pdf-path` | Diff PDF |
| `diff-tex-path` | Diff .tex source |
| `metadata-path` | `metadata.json` |

> **Note:** TeX Live is not bundled with this action. Install it yourself using [zauguin/install-texlive](https://github.com/zauguin/install-texlive) or any other method before running this action. See the example above.

## CLI

```bash
pip install latex-builder

latex-builder build                          # build + diff
latex-builder build -f thesis.tex -c pdflatex --compare-with v1.0.0
latex-builder build --skip-diff              # build only
latex-builder revision                       # generate revision.tex only
```

## Output files

| File | Example |
|------|---------|
| Current PDF | `v1.2.3-abc1234.pdf` |
| Diff PDF | `diff-abc1234-vs-def5678.pdf` |
| Diff source | `diff-abc1234-vs-def5678.tex` |
| Metadata | `metadata.json` |
| Version macros | `revision.tex` |

## Requirements

Python 3.11+, Git, LaTeX (xelatex/pdflatex/lualatex + bibtex + latexdiff).

Install TeX Live separately when using the GitHub Action (see example above).
