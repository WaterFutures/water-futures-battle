# The Battle of the Water Futures 🚰
## Designing the next generation of urban water systems

The Battle of the Water Futures was an initiative organised around the **4th International Joint Conference on Water Distribution Systems Analysis and Computing and Control in the Water Industry** (WDSA/CCWI 2026), held in Paphos (Cyprus), from May 18-21, 2026.
The BWF introduced a testbed for evaluating adaptive methodologies for large-scale WDS planning and management under deep uncertainty.
This testbed provides the basis for generating benchmark problem instance, the first instance was the BWF competition, a challenge set on a hypothetical national grid of the Netherlands.

## Read the Full Details 🔎


- 🌐 **[Testbed website](https://waterfutures.github.io/water-futures-battle/)** — specifications of the testbed, including its equations and models, examples, and guides for using the Python package.
- 🐍 **Python package** — install the package with:

	```bash
	pip install water-futures-battle
	```

- 📄 **[Competition paper (arXiv)](http://arxiv.org/abs/2511.22986)** — background, formulation, and results of the Battle of the Water Futures competition.
- 🗃️ **[Archived competition dataset and history (Zenodo)](https://doi.org/10.5281/zenodo.17698299)** — archived datasets, competition materials, and historical records.

## How to Cite

If you use the Battle of the Water Futures testbed or its implementation in your research, please cite the **[Battle of the Water Futures competition paper](http://arxiv.org/abs/2511.22986)**.

Use the **Cite this repository** button in the About section (right sidebar) to copy a citation for this repository in your preferred format.

## Understand this Repository

This repository contains the testbed implementation, data-generation workflows, example solutions, and competition-analysis tools. Each directory includes its own `README.md` with detailed instructions.

- [`bwf_competition_analysis/`](bwf_competition_analysis/) — scripts and notebooks for visualising competition results, generating figures, and handling survey data.
- [`data/`](data/) — materials and workflows used to generate the initial database.
- [`docs/`](docs/) — source files for building the testbed website and the PDF specification.
- [`examples/`](examples/) — example scripts demonstrating how to use the Battle library.
- [`masterplans/`](masterplans/) — example masterplans developed for the BWF competition.
- [`scripts/`](scripts/) — shell scripts used during the competition, including utilities for tasks such as extending a dataset.
- [`src/water_futures_battle/`](src/water_futures_battle/) — the Python library implementing the Battle of the Water Futures testbed.
- [`tests/`](tests/) — tests for the Battle modules.

## Contributing

Contributions that improve the testbed, examples, documentation, analysis tools, and future benchmark instances are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow and pull-request guidance.

## Roadmap

- Publish the competition paper in a scientific journal and release version 2.0.0 of the testbed.
- Release the testbed through WaterBenchmarkHub.
- Support trigger-based interventions.
- Improve computational performance.
- Extend the modelling of operations.
- Support customisable modules.

## Releases and Versioning

Version 2.0.0 accompanies the publication of the competition paper. Future releases may change the testbed and are not guaranteed to remain compatible with the competition dataset. Record the package and dataset versions used for every experiment.

## Licence

This repository combines content released under three different terms.

### Source code and documentation

The source code and documentation, including the preprocessing scripts in `data/`, are released under the [MIT License](./LICENSE).

### Third-party data

The raw third-party data in `data/` remain subject to the licences set by their original providers (see [`data/README.md`](data/README.md#licensing-and-provenance)).

### BWF competition dataset

The BWF competition dataset, derived from the raw data through the preprocessing scripts, is released under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](data/LICENSE) licence.

## Community Standards

Participation in this project is governed by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Do you have questions?

Check out our [discussion page on GitHub](https://github.com/WaterFutures/water-futures-battle/discussions) or, if you can't find an answer, send us an email to <a href="mailto:battlewaterfutures@kwrwater.nl">battlewaterfutures@kwrwater.nl</a>.

---

*We thank the University of Cyprus and the KIOS Research and Innovation Center for organising WDSA/CCWI 2026, as well as the data providers whose materials were crucial for the competition datasets.*

*This competition was organized by the Water-Futures team.*
*Explore our projects on [GitHub](https://github.com/WaterFutures) and learn more about our team and work on our [website](https://waterfutures.eu/).*

*Water-Futures has received funding from the European Research Council (ERC) under the European Union’s Horizon 2020 research and innovation program (Grant Agreement No. 951424).*
