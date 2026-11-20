# dotdoc

Make Graphviz drawings a navigable part of your documentation: nodes link to their API entries, with previews on hover.

```python exec="on" html="1" source="material-block" result="html"
import graphviz

from dotdoc import autoref, graph_html

drawing = graphviz.Digraph(graph_attr={"rankdir": "LR"}, node_attr={"shape": "box"})
drawing.node("autoref", URL=autoref("dotdoc.html.autoref"))
drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
drawing.edge("autoref", "graph_html")

print(graph_html(drawing))
```

Hover over a node's name to preview its API entry, and click it to go there.

!!! warning "Only tested with Zensical"

    dotdoc has only been tested on sites built with [Zensical](https://zensical.org).
    If you'd like to use it with Sphinx, MkDocs 2, or anywhere else, please [open an issue](https://github.com/jmarshrossney/dotdoc/issues), or better still a pull request.

## Installation

=== "uv"

    ```sh
    uv add dotdoc
    ```

=== "pip"

    ```sh
    pip install dotdoc
    ```

Rendering needs Graphviz's `dot` program, from your system's package manager.
For Apache Hamilton DAGs, see [Hamilton](hamilton.md).
