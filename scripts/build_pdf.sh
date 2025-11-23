#!/bin/bash

# The desired output filename
OUTPUT_PDF="Zanutto_et_al-2025-battle_water_futures-preprint.pdf"

# The specific list of Markdown files, in the desired order, with respect to the docs/
# folder.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DOCS_DIR="${SCRIPT_DIR}/../docs"
OUT_DIR="${SCRIPT_DIR}/.."

INPUT_FILES=(
  "motivation.md"
  "problem/index.md"
  #"problem/external-drivers/index.md"
  #"solution/index.md" 
  #"conclusion/summary.md"
)

FILES_FULLPATH=()
for file in "${INPUT_FILES[@]}"; do
    FILES_FULLPATH+=("${DOCS_DIR}/$file")
done

# Pandoc Arguments for High-Quality PDF
PANDOC_ARGS=(
  "--from" "markdown"           # Input format is Markdown
  "--pdf-engine" "pdflatex"     # Use pdflatex for better PDF quality
  "--toc"                       # Generate a Table of Contents
  "--number-sections"           # Automatically number headings
  "-o" "$OUT_DIR/$OUTPUT_PDF"            # Output to the defined PDF file
)

# --- Execution ---

echo "--- Pandoc PDF Builder ---"
echo "Input Files: ${INPUT_FILES[*]}"

# Execute Pandoc
# The structure is: pandoc [INPUT_FILES] [PANDOC_ARGS]
pandoc "${FILES_FULLPATH[@]}" "${PANDOC_ARGS[@]}"

# Check the exit status of the previous command (Pandoc)
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Success! The PDF has been created at: ${OUT_DIR}$OUTPUT_PDF"
else
  echo ""
  echo "❌ Error: Pandoc failed to generate the PDF."
fi

