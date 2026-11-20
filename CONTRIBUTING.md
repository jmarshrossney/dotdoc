# Contributing

Contributions are welcome.
Please open a Pull Request against the `main` branch.

## Getting started

This project uses [`uv`](https://docs.astral.sh/uv/). 
Install the project and its development dependencies with

```sh
uv sync
```

A [`justfile`](justfile) provides the common tasks. Run everything with

```sh
uv run just
```

or individually:

| Command | What it does |
|---|---|
| `just lint` | `ruff format`, `ruff check --fix` |
| `just lint-check` | Non-mutating variant, used by CI |
| `just typecheck` | `pyright` |
| `just test` | `pytest` |
| `just test-cov` | `pytest` with coverage, failing under 90% |
| `just doctest` | Run the doctest examples in `src/` |
| `just docs` | `zensical build` |
| `just docs-serve` | The same, with a live-reloading local server |
| `just bump` | Pin the uv hook and `uv_build` to the installed uv, update the ruff and pyright hooks, relock |

The recipes call tools installed in the project's virtual environment, so prefix each command with `uv run`, e.g. `uv run just test`, unless that environment is activated (for example by direnv).

Consider installing [`pre-commit`](https://pre-commit.com/) so that the hooks in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) run before each commit:

```sh
uv tool install pre-commit
pre-commit install
```

## Documentation

The documentation is built with [Zensical](https://zensical.org/) from the Markdown in `docs/`, plus an API reference generated from docstrings by [mkdocstrings](https://mkdocstrings.github.io/).

A `python exec="on"` block in `docs/` runs during the build, through [markdown-exec](https://pawamoy.github.io/markdown-exec/), and its output goes into the page.
The build passes even when a block raises, so `tests/test_docs.py` runs every such block.

Preview the site locally with `just docs-serve`.

## Style

- Ruff enforces formatting and lint; see `[tool.ruff]` in `pyproject.toml`.
- Public functions and classes in `src/` need docstrings, in [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
- Type annotations are expected; `pyright` runs over `src/` and `tests/`.
