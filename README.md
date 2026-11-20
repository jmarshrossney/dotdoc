# dotdoc

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
