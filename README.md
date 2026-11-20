# dotdoc

Make Graphviz drawings a navigable part of your documentation: nodes link to their API entries, with previews on hover.
Includes styles for Hamilton graphs.

## Installation

```sh
pip install dotdoc
```

## Usage

Give a Graphviz node a `URL` and render the drawing with `graph_html`:

```python
import graphviz
from dotdoc import autoref, graph_html

drawing = graphviz.Digraph()
drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
html = graph_html(drawing)  # write into a page at build time
```

The node's name then links to its mkdocstrings entry, whatever the site's URL style, and Zensical and Material for MkDocs preview that entry on hover.
For Apache Hamilton DAGs, `dotdoc.hamilton` links each node to the function that defines it:

```sh
pip install "dotdoc[hamilton]"
```

See the [documentation](https://jmarshrossney.github.io/dotdoc)
for more.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: `uv sync`, then `uv run just`.

```
uv run just                  # lint, typecheck, test, docs
uv run just lint             # ruff format, ruff check --fix
uv run just lint-check       # non-mutating variant, used by CI
uv run just typecheck        # pyright
uv run just test             # pytest
uv run just test-cov         # pytest with coverage, fails under 90%
uv run just doctest          # run the doctest examples in src/
uv run just docs             # zensical build
uv run just docs-serve       # the same, with a live-reloading local server
uv run just bump             # re-pin uv and the pre-commit hooks to the installed uv
```

---

Generated from a [Copier](https://copier.readthedocs.io/) template, recorded in
`.copier-answers.yml`. Pull later template changes with `copier update`.
