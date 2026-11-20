"""Render a Graphviz drawing as an HTML fragment for a documentation page.

`graph_html` inlines the SVG and lays an invisible HTML link over the name of
each node with a `URL` attribute, so that the name is a link and a theme's link
previews work on it.

A node's `URL` may name an mkdocstrings identifier rather than a URL, through
`autoref`, and the documentation build then writes the link.
"""

import html
import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

import graphviz

__all__ = ["AUTOREF_PREFIX", "PREVIEW_OVERLAY", "autoref", "graph_html"]

PREVIEW_OVERLAY: Mapping[str, str] = MappingProxyType({"data-preview": ""})
"""Overlay attributes that turn on instant previews in Zensical and Material for
MkDocs."""

AUTOREF_PREFIX = "autoref:"
"""Marks a node's `URL` as an identifier for the documentation build to resolve."""

_SVG_SIZE_RE = re.compile(r'\s(?:width|height)="(?P<value>[\d.]+)pt"')
_VIEWBOX_RE = re.compile(r'viewBox="(?P<box>[^"]+)"')
_TRANSFORM_RE = re.compile(
    r'id="graph0"[^>]*transform="scale\((?P<scale>[^)]+)\)'
    r'[^"]*translate\((?P<translate>[^)]+)\)"'
)

# Themes underline every link in page content, which includes the `<a>` that
# Graphviz wraps around any node with a tooltip. Only a linked node's name (its
# first label line), which its overlay covers, keeps the underline. No square
# brackets anywhere in the fragment: Markdown escapes them, even inside
# `<style>` and attributes.
_CSS = (
    ".dotdoc-graph svg a{text-decoration:none}"
    ".dotdoc-graph svg a.dotdoc-link text:first-of-type{text-decoration:underline}"
    # An unfilled shape shows its tooltip only on its outline otherwise.
    ".dotdoc-graph svg a *{pointer-events:visible}"
)

# Full screen: opaque, scrollable, and the drawing as wide as fits. The button
# label is swapped by CSS, so leaving full screen with Esc updates it too.
_FULLSCREEN_CSS = (
    ".dotdoc-fullscreen{margin-bottom:0.5em}"
    ".dotdoc-graph:fullscreen{overflow:auto;padding:1.5rem;"
    "background:#fff;color:#000}"
    ".dotdoc-graph:fullscreen .dotdoc-drawing"
    "{width:min(100%,1400px);max-width:none!important;margin:0 auto}"
    ".dotdoc-graph:fullscreen .dotdoc-enter,"
    ".dotdoc-graph:not(:fullscreen) .dotdoc-exit{display:none}"
)

# An inline handler rather than a script, so it needs no JavaScript file and
# survives a theme's instant navigation, which does not rerun page scripts.
_FULLSCREEN_BUTTON = (
    '<button type="button" class="dotdoc-fullscreen md-button" onclick="'
    "var f=this.closest('.dotdoc-graph');"
    "if(document.fullscreenElement===f)document.exitFullscreen();"
    "else if(document.fullscreenEnabled)f.requestFullscreen()"
    '"><span class="dotdoc-enter">Full screen</span>'
    '<span class="dotdoc-exit">Exit full screen</span></button>'
)


_SVG_NODE_LINK_RE = re.compile(r'(?P<start><g id="a_node\d+"><a) xlink:href="[^"]*"')


def autoref(identifier: str) -> str:
    """Return a node `URL` that links to an identifier's documentation.

    `graph_html` writes the node's overlay as an `<autoref>` element, which
    mkdocs-autorefs, and Zensical's own autorefs, replace with a link to the
    identifier's entry, relative to the page and whatever the site's URL
    style. An identifier the build cannot find is reported as a warning.
    The links work only in a page those tools build: in a notebook, for
    instance, they lead nowhere.

    Args:
        identifier: What the documentation registers the entry under; for
            mkdocstrings, an object's dotted path, such as
            `"dotdoc.html.graph_html"`.

    Returns:
        The identifier, prefixed with `AUTOREF_PREFIX`.

    Examples:
        >>> autoref("dotdoc.html.graph_html")
        'autoref:dotdoc.html.graph_html'
    """
    return AUTOREF_PREFIX + identifier


def _identifier(url: str) -> str | None:
    if url.startswith(AUTOREF_PREFIX):
        return url.removeprefix(AUTOREF_PREFIX)
    return None


def _unlink_nodes(svg: str) -> str:
    """Drop the SVG's node links, which the overlays replace.

    The `<a>` stays, without its `href`, for the tooltip Graphviz gives it.
    """
    return _SVG_NODE_LINK_RE.sub(r'\g<start> class="dotdoc-link"', svg)


def _numbers(text: str) -> list[float]:
    return [float(v) for v in text.replace(",", " ").split()]


def _name_box(obj: Mapping[str, Any]) -> tuple[float, float, float, float]:
    """Return `(left, top, width, height)` of a node's first label line.

    In Graphviz's layout coordinates: points, origin at the bottom left. The
    first text drawn in the label is taken to be the node's name; its height is
    taken from the font size. A node with no text falls back to its whole box.
    """
    size = 14.0
    for op in obj.get("_ldraw_", []):
        if op["op"] == "F":
            size = float(op["size"])
        elif op["op"] == "T":
            (x, y), width = op["pt"], float(op["width"])
            x -= {"l": 0.0, "c": width / 2, "r": width}[op["align"]]
            return x, y + 0.8 * size, width, size
    x, y = _numbers(obj["pos"])
    w, h = float(obj["width"]) * 72, float(obj["height"]) * 72
    return x - w / 2, y + h / 2, w, h


def _name(obj: Mapping[str, Any]) -> str:
    """Return a node's first label line, or its id if it has no text."""
    for op in obj.get("_ldraw_", []):
        if op["op"] == "T":
            return op["text"]
    return obj["name"]


def _overlays(
    drawing: graphviz.Source | graphviz.Graph | graphviz.Digraph,
    svg: str,
    attrs: Mapping[str, str] | None,
) -> list[str]:
    """Return an absolutely positioned link over each linked node's name.

    Name boxes come from Graphviz's JSON layout and are mapped through the
    SVG's `graph0` transform into percentages of its `viewBox`, so they scale
    with the drawing.
    """
    viewbox, transform = _VIEWBOX_RE.search(svg), _TRANSFORM_RE.search(svg)
    if viewbox is None or transform is None:
        raise ValueError("Graphviz drew an SVG without the expected layout.")
    vx, vy, vw, vh = _numbers(viewbox["box"])
    sx, sy = _numbers(transform["scale"])
    tx, ty = _numbers(transform["translate"])
    layout = json.loads(drawing.pipe(format="json", encoding="utf-8"))
    extra = "".join(f' {k}="{html.escape(v)}"' for k, v in (attrs or {}).items())
    overlays = []
    for obj in layout.get("objects", []):
        url = obj.get("URL")
        if not url or "pos" not in obj:
            continue
        x, y, w, h = _name_box(obj)
        left = (sx * (x + tx) - vx) / vw * 100
        top = (sy * (ty - y) - vy) / vh * 100
        # `font-size:0` hides any icon a theme appends to the link.
        box = (
            f"position:absolute;font-size:0;left:{left:.3f}%;top:{top:.3f}%;"
            f"width:{sx * w / vw * 100:.3f}%;height:{sy * h / vh * 100:.3f}%"
        )
        rest = f'aria-label="{html.escape(_name(obj))}" style="{box}"{extra}'
        identifier = _identifier(url)
        if identifier is None:
            overlays.append(f'<a href="{html.escape(url)}" {rest}></a>')
        else:
            identifier = html.escape(identifier)
            overlays.append(f'<autoref identifier="{identifier}" {rest}></autoref>')
    return overlays


def graph_html(
    drawing: graphviz.Source | graphviz.Graph | graphviz.Digraph,
    *,
    overlay: Mapping[str, str] | None = PREVIEW_OVERLAY,
    fullscreen: bool = False,
) -> str:
    """Render a Graphviz drawing as an HTML fragment for a documentation page.

    The SVG is inlined, so its tooltips work (an SVG shown through `<img>` has
    none), and it scales down to fit the page. A node is linked by giving it a
    `URL` attribute. Its name, taken to be the first line of its label, is then
    the link: an invisible HTML link, carrying `overlay`'s attributes, is laid
    over it and the name is underlined, whatever the theme does to links. The
    rest of the node is not a link, so following one is always the same
    gesture as previewing it, and themes that preview a link's target on hover
    only handle HTML links anyway. The overlays must be in the page when it
    loads, so write the fragment into the page source or a notebook's output
    rather than adding it from a script.

    A URL is written into the page as it is, so it must work from the built
    page; a URL made by `autoref` names an identifier for the documentation
    build to resolve, which works in any URL style. Links on edges and graphs
    are left to the SVG.

    Args:
        drawing: The Graphviz drawing to render. Any graph works, directed or
            not, cycles included.
        overlay: Extra attributes for each overlay link, or `None` for none.
            The default turns on instant previews in Zensical and Material for
            MkDocs.
        fullscreen: Add a button above the drawing that shows it full screen.
            The button carries the `md-button` class, so Zensical and Material
            for MkDocs style it; it does nothing in a browser that cannot show
            an element full screen.

    Returns:
        A `<div class="dotdoc-graph">` holding a short stylesheet, the
        optional button, and the SVG with its overlays, with no blank lines, so
        a Markdown page can hold it as one raw HTML block.

    Raises:
        ValueError: If Graphviz drew an SVG without the layout the overlays are
            positioned from.

    Examples:
        In a marimo notebook exported to a documentation page:

        ```python
        drawing = graphviz.Digraph()
        drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
        mo.Html(graph_html(drawing))
        ```
    """
    svg = drawing.pipe(format="svg", encoding="utf-8")
    svg = svg[svg.index("<svg") :]
    root_end = svg.index(">")
    root = svg[:root_end]
    width = next((m["value"] for m in _SVG_SIZE_RE.finditer(root)), None)
    root = _SVG_SIZE_RE.sub("", root) + ' style="display:block;width:100%;height:auto"'
    svg = "\n".join(line for line in (root + svg[root_end:]).splitlines() if line)
    overlays = _overlays(drawing, svg, overlay)
    svg = _unlink_nodes(svg)
    size = f"max-width:{width}pt;" if width is not None else ""
    css = _CSS + (_FULLSCREEN_CSS if fullscreen else "")
    return "".join(
        [
            '<div class="dotdoc-graph">',
            f"<style>{css}</style>",
            _FULLSCREEN_BUTTON if fullscreen else "",
            f'<div class="dotdoc-drawing" style="position:relative;{size}">',
            svg,
            *overlays,
            "</div></div>",
        ]
    )
