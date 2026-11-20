# dotdoc

Make Graphviz drawings a navigable part of your documentation: nodes link to their API entries, with previews on hover.
Includes styles for Hamilton graphs.

Built with
[uv](https://docs.astral.sh/uv/),
[just](https://just.systems/),
[ruff](https://docs.astral.sh/ruff/),
[pyright](https://github.com/microsoft/pyright),
[pytest](https://pytest.org/) and
[zensical](https://zensical.org/).

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
html = graph_html(drawing)  # write into a page, or return mo.Html(html) from marimo
```

The node's name then links to its mkdocstrings entry, whatever the site's URL style, and Zensical and Material for MkDocs preview that entry on hover.
For Apache Hamilton DAGs, `dotdoc.hamilton` links each node to the function that defines it:

```sh
pip install "dotdoc[hamilton]"
```

See [Getting started](getting-started.md) for more, the [example](example.md)
for a worked notebook, and the [API reference](api.md) for the full interface.
