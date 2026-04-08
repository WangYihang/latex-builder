#!/bin/bash
set -eo pipefail

# Map GitHub Action inputs (environment variables) to CLI arguments.
# When not running as a GitHub Action, falls back to direct CLI usage.

REPO="${GITHUB_WORKSPACE:-.}"
OUTPUT_DIR="${INPUT_OUTPUT_DIR:-output}"

ARGS=("build" "$REPO")
ARGS+=("-f" "${INPUT_TEX_FILE:-main.tex}")
ARGS+=("-c" "${INPUT_COMPILER:-xelatex}")
ARGS+=("-o" "$OUTPUT_DIR")
ARGS+=("-t" "${INPUT_TIMEOUT:-300}")
ARGS+=("--revision-file" "${INPUT_REVISION_FILE:-variables/revision.tex}")

[[ -n "$INPUT_COMPARE_WITH" ]] && ARGS+=("--compare-with" "$INPUT_COMPARE_WITH")
[[ "$INPUT_SKIP_DIFF" == "true" ]] && ARGS+=("--skip-diff")
[[ "$INPUT_DIFF_ONLY" == "true" ]] && ARGS+=("--diff-only")
[[ "$INPUT_VERBOSE" == "true" ]] && ARGS+=("-v")

echo "::group::latex-builder"
uv run latex-builder "${ARGS[@]}"
EXIT_CODE=$?
echo "::endgroup::"

# --- Write GitHub Action outputs ---
if [[ -n "$GITHUB_OUTPUT" ]]; then
  # Version name from metadata.json
  METADATA="$OUTPUT_DIR/metadata.json"
  if [[ -f "$METADATA" ]]; then
    VERSION_NAME=$(python3 -c "import json; m=json.load(open('$METADATA')); print(m['current']['version']['display_name'])" 2>/dev/null || echo "")
    DIFF_STEM=$(python3 -c "import json; m=json.load(open('$METADATA')); print(m['diff_files']['tex'])" 2>/dev/null || echo "")
    DIFF_PDF=$(python3 -c "import json; m=json.load(open('$METADATA')); print(m['diff_files']['pdf'])" 2>/dev/null || echo "")

    echo "version-name=$VERSION_NAME" >> "$GITHUB_OUTPUT"
    echo "metadata-path=$METADATA" >> "$GITHUB_OUTPUT"

    # PDF path: version-name.pdf
    if [[ -n "$VERSION_NAME" && -f "$OUTPUT_DIR/$VERSION_NAME.pdf" ]]; then
      echo "pdf-path=$OUTPUT_DIR/$VERSION_NAME.pdf" >> "$GITHUB_OUTPUT"
    fi

    # Diff files
    if [[ -n "$DIFF_STEM" && -f "$OUTPUT_DIR/$DIFF_STEM" ]]; then
      echo "diff-tex-path=$OUTPUT_DIR/$DIFF_STEM" >> "$GITHUB_OUTPUT"
    fi
    if [[ -n "$DIFF_PDF" && -f "$OUTPUT_DIR/$DIFF_PDF" ]]; then
      echo "diff-pdf-path=$OUTPUT_DIR/$DIFF_PDF" >> "$GITHUB_OUTPUT"
    fi
  fi
fi

exit $EXIT_CODE
