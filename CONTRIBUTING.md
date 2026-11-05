# Contributing to the Battle of the Water Futures

Contributions to the testbed, examples, documentation, analysis tools, and future benchmark instances are welcome.

## Getting Started

Clone the repository and create a branch for your work:

```bash
git clone https://github.com/WaterFutures/water-futures-battle.git
cd water-futures-battle
git switch -c feature/short-description
```

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python environment and dependencies. Install uv, then create the development environment:

```bash
uv sync --group dev
```

Run the test suite before submitting changes:

```bash
uv run pytest
```

## Submitting Changes

1. Create a focused branch from the current default branch.
2. Make the smallest change that addresses the issue or improvement.
3. Add or update tests when behaviour changes.
4. Run the relevant tests and update documentation where needed.
5. Open a pull request that explains the motivation, implementation, and validation performed.

Please use GitHub Discussions for questions and feature ideas, and GitHub Issues for reproducible bugs or concrete enhancement proposals.

## Data Contributions

Do not submit third-party data unless you have the right to redistribute it. Contributions that add or modify data must document its source, applicable licence or terms, required attribution, and any restrictions in [`data/README.md`](data/README.md).

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).