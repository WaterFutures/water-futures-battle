
# --- Configuration Variables ---


# Output filenames (in project root)
OUTPUT_DATA := ../water_futures_battle-data.zip
OUTPUT_PDF := ../water_futures_battle-preprint.pdf
OUTPUT_LATEX := ../water_futures_battle-source.tex
OUTPUT_LATEX_CLEANED := ../water_futures_battle-source_cleaned.tex
OUTPUT_SUBMISSION := ../water_futures_battle-arxiv_submission.zip
OUTPUT_WEBSITE := ../water_futures_battle-website.zip

# Documentation source directory (current working dir for builds)
DATA_DIR := ../data
DOCS_DIR := ../docs

MATCH_STR="../../assets/img/"
REPL_STR="./"

# --- Input Files ---

# List of Markdown files, relative to docs/
MARKDOWN_FILES = \
	paper/exec-summary.md \
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
	paper/notation.md \
	paper/references.md \
	paper/appendix.md

DATA_FILES = \
	configuration.yaml \
	masterplan.yaml \
	epanet-networks/*-2025.inp \
	epanet-networks/README.md \
	connections/connections-static_properties.xlsx \
	jurisdictions/jurisdictions-static_properties.xlsx \
	jurisdictions/municipalities-dynamic_properties.xlsx \
	nrw_model/nrw_model-dynamic_properties.xlsx \
	pipes/pipe_options-static_properties.xlsx \
	pipes/pipe_options-dynamic_properties.xlsx \
	pumping_stations/pumping_stations-static_properties.xlsx \
	pumps/pump_options-static_properties.xlsx \
	pumps/pump_options-dynamic_properties.xlsx \
	sources/sources-static_properties.xlsx \
	sources/desalination-dynamic_properties.xlsx \
	sources/groundwater-dynamic_properties.xlsx \
	sources/surface_water-dynamic_properties.xlsx \
	water_demand_model/water_demand_model-dynamic_properties.xlsx \
	water_utilities/water_utilities-static_properties.xlsx \
	raw-data/

# --- Dependencies ---

DEPENDENCIES := \
	$(MARKDOWN_FILES) \
	paper/metadata.yaml

# --- Pandoc Arguments ---

PANDOC_COMMON_ARGS := \
	--from markdown \
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

.PHONY: all data latex pdf website clean

all: data latex pdf website

data:
	cd $(DATA_DIR) && zip -r $(OUTPUT_DATA) $(DATA_FILES)

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