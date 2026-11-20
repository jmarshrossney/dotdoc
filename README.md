# dotdoc

[![PyPI version](https://img.shields.io/pypi/v/dotdoc)](https://pypi.org/project/dotdoc/)
[![Python versions](https://img.shields.io/pypi/pyversions/dotdoc)](https://pypi.org/project/dotdoc/)
[![CI](https://github.com/jmarshrossney/dotdoc/actions/workflows/ci.yml/badge.svg)](https://github.com/jmarshrossney/dotdoc/actions/workflows/ci.yml)
[![Docs](https://github.com/jmarshrossney/dotdoc/actions/workflows/docs.yml/badge.svg)](https://jmarshrossney.github.io/dotdoc)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/jmarshrossney/dotdoc/blob/main/LICENSE)

Make Graphviz drawings a navigable part of your documentation: nodes link to their API entries, with previews on hover.

```python
import graphviz

from dotdoc import autoref, graph_html

drawing = graphviz.Digraph(graph_attr={"rankdir": "LR"}, node_attr={"shape": "box"})
drawing.node("autoref", URL=autoref("dotdoc.html.autoref"))
drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
drawing.edge("autoref", "graph_html")

print(graph_html(drawing))
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmarshrossney/dotdoc/main/.github/assets/example-dark.svg">
  <img alt="A drawing of two boxes, autoref and graph_html, joined by an arrow" src="https://raw.githubusercontent.com/jmarshrossney/dotdoc/main/.github/assets/example-light.svg">
</picture>

In the [documentation](https://jmarshrossney.github.io/dotdoc), each node's name links to its API entry, with a preview on hover.

> [!IMPORTANT]
> dotdoc has only been tested on sites built with [Zensical](https://zensical.org).
> If you'd like to use it with Sphinx, MkDocs 2, or anywhere else, please [open an issue](https://github.com/jmarshrossney/dotdoc/issues), or better still a pull request.

## Installation

```sh
uv add dotdoc
```

or

```sh
pip install dotdoc
```

Rendering needs Graphviz's `dot` program, from your system's package manager.
For Apache Hamilton DAGs, see [Hamilton](https://jmarshrossney.github.io/dotdoc/hamilton.html).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md).
