
# --- Configuration Variables ---


# Output filenames (in project root)
OUTPUT_PDF := ../water_futures_battle-preprint.pdf
OUTPUT_LATEX := ../water_futures_battle-source.tex
OUTPUT_LATEX_CLEANED := ../water_futures_battle-source_cleaned.tex
OUTPUT_SUBMISSION := ../water_futures_battle-arxiv_submission.zip
OUTPUT_WEBSITE := ../water_futures_battle-website.zip

# Documentation source directory (current working dir for builds)
DOCS_DIR := ../docs

MATCH_STR="../../assets/img/"
REPL_STR="./"

# --- Input Files ---

# List of Markdown files, relative to docs/
MARKDOWN_FILES = \
	motivation.md \
	problem/index.md \
	problem/system-description/index.md \
	problem/system-description/water-utilities.md \
	problem/system-description/municipalities.md \
	problem/system-description/sources.md \
	problem/system-description/pumping-stations.md \
	problem/system-description/pipes.md \
	problem/external-drivers/index.md \
	problem/external-drivers/climate.md \
	problem/external-drivers/energy-system.md \
	problem/external-drivers/economy-financing.md \
	problem/system-interventions/index.md \
	problem/system-requirements/index.md \
	paper/acknowledgement.md \
	paper/data-availability-statement.md \
	paper/references.md \
	paper/appendix.md

# --- Dependencies ---

DEPENDENCIES := \
	$(MARKDOWN_FILES) \
	paper/metadata.yaml

# --- Pandoc Arguments ---

PANDOC_COMMON_ARGS := \
	--from markdown \
	--toc \
	--number-sections \
	--metadata-file=paper/metadata.yaml \
	--resource-path=problem/system-description \
	--filter bin/pandoc-crossref \
	--citeproc # Careful: pandoc crossref must go before citeproc

PANDOC_LATEX_ARGS := \
	--to=latex \
	--standalone

PANDOC_PDF_ARGS := \
	--pdf-engine=pdflatex

# --- Build Targets ---

.PHONY: all latex pdf website clean

all: latex pdf website

latex:
	cd $(DOCS_DIR) && pandoc -o $(OUTPUT_LATEX) $(PANDOC_COMMON_ARGS) $(PANDOC_LATEX_ARGS) $(MARKDOWN_FILES)
	cp $(OUTPUT_LATEX) $(OUTPUT_LATEX_CLEANED)
	sed -i "s|$(MATCH_STR)|$(REPL_STR)|g" $(OUTPUT_LATEX_CLEANED)
	cd $(DOCS_DIR) && zip -j $(OUTPUT_SUBMISSION) $(OUTPUT_LATEX_CLEANED) assets/img/*

pdf:
	cd $(DOCS_DIR) && pandoc -o $(OUTPUT_PDF) $(PANDOC_COMMON_ARGS) $(PANDOC_PDF_ARGS) $(MARKDOWN_FILES)

website:
	cd $(DOCS_DIR) && bundle exec jekyll build
	cd $(DOCS_DIR) && zip -r $(OUTPUT_WEBSITE) ./_site


clean:
	rm -f $(OUTPUT_LATEX) $(OUTPUT_PDF) $(OUTPUT_WEBSITE)
	cd $(DOCS_DIR) && rm -rf ./_site/