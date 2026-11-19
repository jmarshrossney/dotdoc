# dotdoc

Make Graphviz drawings a navigable part of your documentation: nodes link to their API entries, with previews on hover.

## Installation

```sh
pip install dotdoc
```

## Usage

```python
from dotdoc import greet

greet("world")
```

See the [documentation](https://jmarshrossney.github.io/dotdoc)
for more.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: `uv sync`, then `uv run just`.

```
uv run just                  # lint, typecheck, test, check-examples, docs
uv run just lint             # ruff format, marimo check --fix, ruff check --fix, marimo --strict
uv run just lint-check       # non-mutating variant, used by CI
uv run just check-canonical  # assert the notebooks are in marimo's canonical form
uv run just check-examples   # actually execute the example notebooks
uv run just typecheck        # pyright
uv run just test             # pytest
uv run just test-cov         # pytest with coverage, fails under 90%
uv run just doctest          # run the doctest examples in src/
uv run just docs             # export example notebooks, then zensical build
uv run just docs-serve       # the same, with a live-reloading local server
uv run just bump             # re-pin uv and the pre-commit hooks to the installed uv
```

---

Generated from a [Copier](https://copier.readthedocs.io/) template, recorded in
`.copier-answers.yml`. Pull later template changes with `copier update`.
