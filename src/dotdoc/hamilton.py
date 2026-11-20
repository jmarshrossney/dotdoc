"""Style functions for drawings of Apache Hamilton DAGs.

Hamilton's `Driver` display methods (`display_all_functions`,
`display_upstream_of` and the rest) take a single `custom_style_function`,
called once per node with that node and its class, and returning the node's
Graphviz attributes, its base class and its legend entry. The functions here
build style functions that link nodes to their documentation, give them a
tooltip from their docstring and fill them by a tag; `compose_styles` combines
them with each other and with your own.

Hamilton draws each legend entry with the style of the last node that named
it, so once nodes are linked, every legend swatch carries some node's link and
tooltip. `clean_legend` strips them from the drawing Hamilton returns.

Needs the `hamilton` extra: `pip install "dotdoc[hamilton]"`.
"""

import inspect
import re
from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING

from hamilton import graph_types
from hamilton.driver import Driver

from .html import autoref

if TYPE_CHECKING:
    import graphviz

__all__ = [
    "LinkFunction",
    "StyleFunction",
    "TooltipFunction",
    "api_autoref",
    "clean_legend",
    "compose_styles",
    "fill_by_tag",
    "link_style",
    "summary",
    "tooltip_style",
]

type StyleFunction = Callable[..., tuple[dict[str, str], str | None, str | None]]
"""A Hamilton `custom_style_function`.

It is called with the keyword arguments `node` (a `HamiltonNode`) and
`node_class` (a string), and returns `(attributes, base_class, legend_entry)`.
"""

type LinkFunction = Callable[[graph_types.HamiltonNode, Callable | None], str | None]
"""Receives a node and the function that defines it, and returns the URL of its
documentation, or `None` for no link.

The function is `None` for inputs, config, and field nodes from
`@extract_fields`, which share their parent's function.
"""

type TooltipFunction = Callable[
    [graph_types.HamiltonNode, Callable | None], str | Sequence[str] | None
]
"""Receives a node and the function that defines it, and returns its tooltip,
or `None` for no tooltip.

A string is one line; a sequence of strings is one line each. The function is
`None` for inputs, config, and field nodes from `@extract_fields`, which share
their parent's function.
"""


def compose_styles(*style_functions: StyleFunction) -> StyleFunction:
    """Combine Hamilton style functions into one.

    Hamilton's display methods take a single style function. Each node's
    attributes are merged left to right, so a later function overrides an
    earlier one's. The base class and legend entry come from the last function
    that names a legend entry.

    Args:
        *style_functions: The style functions to combine, in order.

    Returns:
        A style function to pass to Hamilton as `custom_style_function`.
    """

    def composed(
        *, node: graph_types.HamiltonNode, node_class: str
    ) -> tuple[dict[str, str], str | None, str | None]:
        style: dict[str, str] = {}
        base: str | None = node_class
        legend: str | None = None
        for function in style_functions:
            attrs, fn_base, fn_legend = function(node=node, node_class=node_class)
            style.update(attrs)
            if fn_legend is not None:
                base, legend = fn_base, fn_legend
        return style, base, legend

    return composed


def _own_functions(dr: Driver) -> dict[str, Callable]:
    """Return `node -> function` for the nodes a function itself defines.

    A field node (one per `@extract_fields` output) shares its originating
    function with the node it depends on, so it is left out; external inputs,
    which Hamilton gives the consuming function as their originating function,
    are left out too.
    """
    own: dict[str, Callable] = {}
    for n in dr.graph.nodes.values():
        if n.user_defined or not n.originating_functions:
            continue
        fn = n.originating_functions[0]
        if any(
            not dep.user_defined
            and dep.originating_functions
            and dep.originating_functions[0] is fn
            for dep in n.dependencies
        ):
            continue
        own[n.name] = fn
    return own


def _node_values[T](
    dr: Driver, value: Callable[[graph_types.HamiltonNode, Callable | None], T]
) -> dict[str, T]:
    own = _own_functions(dr)
    return {
        name: value(graph_types.HamiltonNode.from_node(n), own.get(name))
        for name, n in dr.graph.nodes.items()
    }


def _api_link(node: graph_types.HamiltonNode, function: Callable | None) -> str | None:
    return None if function is None else api_autoref(function)


def _summary_tooltip(
    node: graph_types.HamiltonNode, function: Callable | None
) -> str | None:
    return None if function is None else summary(function)


def _attribute_style(attribute: str, values: Mapping[str, str]) -> StyleFunction:
    def style(
        *, node: graph_types.HamiltonNode, node_class: str
    ) -> tuple[dict[str, str], str | None, str | None]:
        value = values.get(node.name)
        return ({} if value is None else {attribute: value}), node_class, None

    return style


def api_autoref(function: Callable) -> str:
    """Link a function to its mkdocstrings entry, wherever that is in the site.

    The identifier is the dotted path of the function where it is defined,
    `function.__module__` then `function.__qualname__`, which is where
    mkdocstrings registers it when that module is documented. See
    `dotdoc.html.autoref`.

    Args:
        function: The function to link to.

    Returns:
        A `URL` for `graph_html` to write as an `<autoref>` element.

    Examples:
        >>> from dotdoc import graph_html
        >>> api_autoref(graph_html)
        'autoref:dotdoc.html.graph_html'
    """
    return autoref(f"{function.__module__}.{function.__qualname__}")


def link_style(dr: Driver, link: LinkFunction | None = None) -> StyleFunction:
    """Build a style function that links nodes to their documentation.

    Each node gets `URL` set to `link(node, function)`, which
    `dotdoc.html.graph_html` makes the node's name link to.

    Args:
        dr: The driver whose DAG will be drawn.
        link: Receives a node and the function that defines it, or `None` for
            inputs, config and field nodes from `@extract_fields`, and returns
            its URL, or `None` for no link. The default links each node a
            function defines to the function's mkdocstrings entry, through
            `api_autoref`; a function documented under another path, such as
            where a package re-exports it, needs a link function of its own.

    Returns:
        A style function to pass to Hamilton, alone or through
        `compose_styles`.

    Examples:
        Link each node to its function's mkdocstrings entry:

        ```python
        digraph = dr.display_all_functions(custom_style_function=link_style(dr))
        ```

        Or to a page outside the documentation build:

        ```python
        def source_url(node, fn):
            if fn is not None:
                return f"https://example.org/source/{fn.__module__}.html"

        digraph = dr.display_all_functions(
            custom_style_function=link_style(dr, source_url)
        )
        ```
    """
    urls = _node_values(dr, link or _api_link)
    return _attribute_style("URL", {k: v for k, v in urls.items() if v is not None})


def summary(function: Callable) -> str | None:
    """Return the first paragraph of a function's docstring, as plain text.

    The paragraph is put on one line and backticks are dropped, since a tooltip
    shows them literally.

    Args:
        function: The function whose docstring to read.

    Returns:
        The summary, or `None` if the function has no docstring.

    Examples:
        >>> def f():
        ...     '''Add one to `x`,
        ...     then double it.
        ...
        ...     More detail.
        ...     '''
        >>> summary(f)
        'Add one to x, then double it.'
    """
    doc = inspect.getdoc(function)
    if not doc:
        return None
    return " ".join(doc.split("\n\n", 1)[0].split()).replace("`", "")


def tooltip_style(dr: Driver, tooltip: TooltipFunction | None = None) -> StyleFunction:
    r"""Build a style function that gives nodes a tooltip.

    Each node gets `tooltip` set to `tooltip(node, function)`, which a browser
    shows on hovering over the node in SVG output. By default that is the
    first paragraph of the docstring of the function that defines the node.
    Backslashes are escaped, so the text is shown as written rather than read
    as Graphviz escape sequences, and the lines of a sequence are joined with
    Graphviz's `\n` line break.

    Args:
        dr: The driver whose DAG will be drawn.
        tooltip: Receives a node and the function that defines it, or `None`
            for inputs, config and field nodes from `@extract_fields`, and
            returns its tooltip as a string or a sequence of lines, or `None`
            for no tooltip. The default gives each node a function defines the
            `summary` of that function.

    Returns:
        A style function to pass to Hamilton, alone or through
        `compose_styles`.
    """
    tips = _node_values(dr, tooltip or _summary_tooltip)
    return _attribute_style(
        "tooltip", {k: _tooltip_text(v) for k, v in tips.items() if v}
    )


def _tooltip_text(lines: str | Sequence[str]) -> str:
    if isinstance(lines, str):
        lines = [lines]
    return "\\n".join(line.replace("\\", "\\\\") for line in lines)


def fill_by_tag(tag: str, colours: Mapping[str, str]) -> StyleFunction:
    """Build a style function that fills nodes by the value of a tag.

    A node whose `tag` value is a key of `colours` is filled with that colour
    and gets a legend entry named after the value. Other nodes are left alone.

    Hamilton names each legend entry's Graphviz node after the entry, so a
    value that is also the name of a node draws that node inside the legend:
    choose values that are not node names.

    Args:
        tag: The name of the tag, as given to Hamilton's `@tag`.
        colours: Tag value to fill colour, in any form Graphviz accepts.

    Returns:
        A style function to pass to Hamilton, alone or through
        `compose_styles`.

    Examples:
        ```python
        style = fill_by_tag("stage", {"clean": "#d9ead3", "model": "#fde9c4"})
        digraph = dr.display_all_functions(custom_style_function=style)
        ```
    """

    def style(
        *, node: graph_types.HamiltonNode, node_class: str
    ) -> tuple[dict[str, str], str | None, str | None]:
        value = node.tags.get(tag)
        if not isinstance(value, str) or value not in colours:
            return {}, node_class, None
        return {"fillcolor": colours[value]}, node_class, value

    return style


_LEGEND_ATTR_RE = re.compile(r'(?:URL|tooltip)="(?:[^"\\]|\\.)*" ?')


def clean_legend(digraph: "graphviz.Digraph") -> "graphviz.Digraph":
    """Drop links and tooltips from the entries of Hamilton's legend, in place.

    Hamilton draws each legend entry with the style of the last node that
    named it, so once nodes are linked, each swatch carries some node's link
    and tooltip. A drawing without a legend is left unchanged.

    Args:
        digraph: A drawing returned by one of Hamilton's display methods.

    Returns:
        `digraph` itself, for chaining.
    """
    in_legend = False
    for i, line in enumerate(digraph.body):
        if "subgraph cluster__legend" in line:
            in_legend = True
        if not in_legend:
            continue
        if line.strip() == "}":
            break
        digraph.body[i] = _LEGEND_ATTR_RE.sub("", line).replace(" ]", "]")
    return digraph
