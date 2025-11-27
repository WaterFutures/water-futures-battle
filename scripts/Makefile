
# --- Configuration Variables ---


# Output filenames (in project root)
OUTPUT_PDF := ../Zanutto_et_al-2025-battle_water_futures-preprint.pdf
OUTPUT_WEBSITE := ../water_futures_battle-website.zip

# Documentation source directory (current working dir for builds)
DOCS_DIR := ../docs

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

PANDOC_ARGS := \
	--from markdown \
	--pdf-engine=pdflatex \
	--toc \
	--number-sections \
	--metadata-file=paper/metadata.yaml \
	--resource-path=problem/system-description \
	--filter bin/pandoc-crossref \
	--citeproc # Careful: pandoc crossref must go before citeproc

# --- Build Targets ---

.PHONY: all pdf website clean

all: pdf website

website:
	cd $(DOCS_DIR) && bundle exec jekyll build
	cd $(DOCS_DIR) && zip -r $(OUTPUT_WEBSITE) ./_site


pdf:
	cd $(DOCS_DIR) && pandoc -o $(OUTPUT_PDF) $(PANDOC_ARGS) $(MARKDOWN_FILES)


clean:
	rm -f $(OUTPUT_PDF) $(OUTPUT_WEBSITE)
	cd $(DOCS_DIR) && rm -rf ./_site/