# --- Configuration Variables ---

# Output filename
OUTPUT_PDF := Zanutto_et_al-2025-battle_water_futures-preprint.pdf
OUTPUT_WEBSITE := water_futures_battle-website.zip

# Define directories relative to the Makefile location (the 'scripts' directory)
# The parent directory (..)
OUT_DIR := ..
# The documentation source directory (../docs)
DOCS_DIR := ../docs

# Full path to the final output PDF
TARGET_PDF := $(OUT_DIR)/$(OUTPUT_PDF)
TARGET_WEBSITE := $(OUT_DIR)/$(OUTPUT_WEBSITE)

# --- Input Files ---

# List of Markdown files, relative to the $(DOCS_DIR)
MARKDOWN_BASENAMES = \
	motivation.md \
	problem/index.md \
	problem/system-description/index.md \
	problem/system-description/water-utilities.md \
	problem/system-description/municipalities/index.md \
	problem/system-description/municipalities/water-demand.md \
	problem/system-description/municipalities/nrw.md \
	problem/system-description/sources.md \
	problem/system-description/pumping-stations.md \
	problem/system-description/pipes.md \
	problem/system-requirements/index.md \
	problem/system-interventions/index.md \
	problem/external-drivers/index.md \
	problem/external-drivers/climate.md \
	problem/external-drivers/energy-system.md \
	problem/external-drivers/economy-financing.md \
	paper/acknowledgement.md

# Convert basenames to full paths for Pandoc dependencies
MARKDOWN_FILES := $(patsubst %, $(DOCS_DIR)/%, $(MARKDOWN_BASENAMES))

# --- Dependencies ---

# All required input files for the PDF build
DEPENDENCIES := \
	$(MARKDOWN_FILES) \
	$(DOCS_DIR)/paper/metadata.yaml

# --- Pandoc Arguments ---

# General Flags
PANDOC_ARGS := \
	--from markdown \
	--pdf-engine=pdflatex \
	--toc \
	--number-sections \
	--metadata-file=$(DOCS_DIR)/paper/metadata.yaml

# --- Build Targets ---

.PHONY: all pdf website clean

all: pdf website

website:
	@cd $(DOCS_DIR) && bundle exec jekyll build
	zip -r $(TARGET_WEBSITE) ../docs/_site/

pdf: $(TARGET_PDF)

# Primary target: Build the PDF
$(TARGET_PDF): $(DEPENDENCIES)
	pandoc -o $@ $(PANDOC_ARGS) $^
	
# Target to remove built files
clean:
	-rm -f $(TARGET_PDF) $(TARGET_WEBSITE)
	-rm -rf ../docs/_site/