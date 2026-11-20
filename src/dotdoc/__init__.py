"""Make Graphviz drawings a navigable part of your documentation.

Give a node a `URL` attribute and render the drawing with `graph_html`: the
node's name then links to that URL, and themes that preview links on hover,
such as Zensical and Material for MkDocs, preview its target too. A `URL` made
by `autoref` names an mkdocstrings identifier instead, and the documentation
build writes the link, whatever the site's URL style.

`dotdoc.hamilton` builds the attributes for drawings of Apache Hamilton DAGs,
linking each node to the documentation of the function that defines it. It
needs the `hamilton` extra.
"""

from .html import AUTOREF_PREFIX, PREVIEW_OVERLAY, DarkColours, autoref, graph_html

__all__ = [
    "AUTOREF_PREFIX",
    "PREVIEW_OVERLAY",
    "DarkColours",
    "autoref",
    "graph_html",
]
