"""Make Graphviz drawings a navigable part of your Zensical documentation.

Give a node a `URL` attribute and render the drawing with `graph_html`: the
node's name then links to that URL, and Zensical previews its target on hover.
A `URL` made by `autoref` names an mkdocstrings identifier instead, and the
documentation build writes the link, whatever the site's URL style. `api_autoref` makes
one for a Python function, and `summary` gives its docstring's first paragraph,
for a tooltip.

`dotdoc.hamilton` builds the attributes for drawings of Apache Hamilton DAGs,
linking each node to the documentation of the function that defines it. It
needs the `hamilton` extra.

dotdoc was written for drawings of Hamilton DAGs in documentation built with
Zensical, and has only been tested there.
"""

from .functions import api_autoref, summary
from .html import AUTOREF_PREFIX, PREVIEW_OVERLAY, DarkColours, autoref, graph_html

__all__ = [
    "AUTOREF_PREFIX",
    "PREVIEW_OVERLAY",
    "DarkColours",
    "api_autoref",
    "autoref",
    "graph_html",
    "summary",
]
