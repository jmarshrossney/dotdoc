"""Render a Graphviz drawing as an HTML fragment for a documentation page.

`graph_html` inlines the SVG and lays an invisible HTML link over the name of
each node with a `URL` attribute, so that the name is a link and a theme's link
previews work on it.

A node's `URL` may name an mkdocstrings identifier rather than a URL, through
`autoref`, and the documentation build then writes the link.
"""

import colorsys
import html
import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Literal

import graphviz

__all__ = ["AUTOREF_PREFIX", "PREVIEW_OVERLAY", "DarkColours", "autoref", "graph_html"]

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
    # Themes colour links too, which `currentColor` in the drawing would pick up.
    ".dotdoc-graph svg a{text-decoration:none;color:inherit}"
    ".dotdoc-graph svg a.dotdoc-link text:first-of-type{text-decoration:underline}"
    # An unfilled shape shows its tooltip only on its outline otherwise.
    ".dotdoc-graph svg a *{pointer-events:visible}"
    # As wide as the page allows, up to the drawing's own size, times the zoom.
    ".dotdoc-scroll{overflow:auto}"
    ".dotdoc-drawing{position:relative;margin:0 auto;"
    "width:calc(min(100%,var(--dotdoc-width,100%))*var(--dotdoc-zoom,1))}"
)

# Expanded, the drawing covers the window, under the theme's previews, and is
# as large as fits it, up or down. Labels are swapped by CSS.
_CONTROLS_CSS = (
    ".dotdoc-controls .md-button{margin:0 0.4em 0.5em 0;padding:0.2em 0.9em}"
    ".dotdoc-graph.dotdoc-expanded{position:fixed;inset:0;z-index:4;"
    "display:flex;flex-direction:column;padding:1rem;"
    "background:var(--md-default-bg-color,#fff)}"
    ".dotdoc-expanded .dotdoc-scroll{flex:1;min-height:0}"
    ".dotdoc-expanded .dotdoc-drawing{width:calc("
    "min(100%,(100vh - 5rem)*var(--dotdoc-ratio,1))*var(--dotdoc-zoom,1))}"
    ".dotdoc-expanded .dotdoc-expand,"
    ".dotdoc-graph:not(.dotdoc-expanded) .dotdoc-close{display:none}"
)


def _zoom(operation: str) -> str:
    return (
        "var d=this.closest('.dotdoc-graph').querySelector('.dotdoc-drawing');"
        "var z=+d.style.getPropertyValue('--dotdoc-zoom')||1;"
        f"d.style.setProperty('--dotdoc-zoom',{operation})"
    )


# Inline handlers rather than a script, so they need no JavaScript file and
# survive a theme's instant navigation, which does not rerun page scripts.
_CONTROLS = (
    '<div class="dotdoc-controls">'
    '<button type="button" class="md-button" '
    "onclick=\"this.closest('.dotdoc-graph').classList.toggle('dotdoc-expanded')\">"
    '<span class="dotdoc-expand">Expand</span>'
    '<span class="dotdoc-close">Close</span></button>'
    '<button type="button" class="md-button" aria-label="Zoom out" '
    f'onclick="{_zoom("Math.max(1,z/1.25)")}">&#8722;</button>'
    '<button type="button" class="md-button" aria-label="Zoom in" '
    f'onclick="{_zoom("Math.min(8,z*1.25)")}">+</button>'
    "</div>"
)

_CLOSE_ON_ESCAPE = (
    " onkeydown=\"if(event.key==='Escape')this.classList.remove('dotdoc-expanded')\""
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


_GROUP_RE = re.compile(r'<g id="[^"]*" class="(?P<kind>node|edge|cluster|graph)"')
_SHAPE_RE = re.compile(r'<(?:ellipse|polygon|polyline|path) fill="(?P<fill>[^"]*)"')
_COLOUR_ATTR_RE = re.compile(r' (?P<attr>fill|stroke)="(?P<colour>[^"]*)"')
_HEX_RE = re.compile(r"#[0-9a-f]{6}")
_BACKGROUND = '<polygon fill="white" stroke="none"'
_NOT_COLOURS = frozenset({"none", "transparent", "black", "currentcolor"})

type DarkColours = Mapping[str, str] | Literal["auto"]
"""Light colours to the colours to draw them in on a dark background, or
`"auto"` to derive one for each colour."""


def _auto_dark(colour: str) -> str | None:
    """Return `colour` with its lightness flipped, or `None` if not hex."""
    colour = "#ffffff" if colour == "white" else colour
    if not _HEX_RE.fullmatch(colour):
        return None
    rgb = (int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
    dark = colorsys.hls_to_rgb(hue, 1 - lightness, saturation)
    return "#" + "".join(f"{round(v * 255):02x}" for v in dark)


def _theme_colours(svg: str, dark: DarkColours | None) -> str:
    """Draw Graphviz's default black in the page's text colour, on no background.

    Strokes and arrowheads drawn in black, and text that sits on the page
    rather than on a filled shape, become `currentColor`, which follows the
    theme's light or dark scheme. Graphviz's white background is dropped.

    A colour with a dark counterpart in `dark` is drawn with CSS
    `light-dark()`, which the browser resolves by the page's `color-scheme`;
    text on a fill with a counterpart becomes `currentColor` too. Text on any
    other fill keeps its colour, to stay readable on light fills.
    """
    table = (
        None
        if dark == "auto" or dark is None
        else {k.lower(): v for k, v in dark.items()}
    )

    def counterpart(colour: str) -> str | None:
        colour = colour.lower()
        if dark is None or colour in _NOT_COLOURS:
            return None
        return _auto_dark(colour) if table is None else table.get(colour)

    def adapt(line: str) -> str:
        line = line.replace('stroke="black"', 'stroke="currentColor"')
        if not line.startswith("<text"):
            line = line.replace('fill="black"', 'fill="currentColor"')
        styles = [
            f"{m['attr']}:light-dark({m['colour']},{html.escape(night)})"
            for m in _COLOUR_ATTR_RE.finditer(line)
            if (night := counterpart(m["colour"])) is not None
        ]
        if not styles:
            return line
        tag, rest = line.split(" ", 1)
        return f'{tag} style="{";".join(styles)}" {rest}'

    lines = []
    kind, keeps_text, shape_seen = "graph", False, False
    for line in svg.splitlines():
        if group := _GROUP_RE.match(line):
            kind, keeps_text, shape_seen = group["kind"], False, False
        elif line.startswith("<text"):
            if not keeps_text and ' fill="' not in line:
                line = line.replace("<text", '<text fill="currentColor"', 1)
            line = adapt(line)
        elif shape := _SHAPE_RE.match(line):
            if kind == "graph" and not shape_seen and line.startswith(_BACKGROUND):
                shape_seen = True
                continue
            if kind in ("node", "cluster") and not shape_seen:
                fill = shape["fill"]
                keeps_text = (
                    fill not in ("none", "transparent") and counterpart(fill) is None
                )
            shape_seen = True
            line = adapt(line)
        lines.append(line)
    return "\n".join(lines)


def _unlink_nodes(svg: str) -> str:
    """Drop the SVG's node links, which the overlays replace.

    The `<a>` stays, without its `href`, for the tooltip Graphviz gives it.
    """
    return _SVG_NODE_LINK_RE.sub(r'\g<start> class="dotdoc-link"', svg)


def _numbers(text: str) -> list[float]:
    return [float(v) for v in text.replace(",", " ").split()]


def _view_box(svg: str) -> list[float]:
    viewbox = _VIEWBOX_RE.search(svg)
    if viewbox is None:
        raise ValueError("Graphviz drew an SVG without the expected layout.")
    return _numbers(viewbox["box"])


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
    vx, vy, vw, vh = _view_box(svg)
    transform = _TRANSFORM_RE.search(svg)
    if transform is None:
        raise ValueError("Graphviz drew an SVG without the expected layout.")
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
    controls: bool = False,
    theme_colours: bool = True,
    dark: DarkColours | None = None,
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
        controls: Add buttons above the drawing that zoom in and out of it
            and expand it to cover the window, for drawings too large to read
            in the page; Esc closes it again. Links and previews work at any
            size. The buttons carry the `md-button` class, so Zensical and
            Material for MkDocs style them.
        theme_colours: Drop Graphviz's white background, and draw what it
            draws in its default black in the page's text colour instead, so
            the drawing follows a theme's light and dark schemes. Text on a
            filled shape keeps its colour, and colours set in the drawing are
            kept. `False` keeps Graphviz's colours.
        dark: Colours to draw in place of the drawing's own on a dark
            background: a mapping from a colour, as given to Graphviz (case
            ignored), to its dark counterpart, in any CSS form; or `"auto"`,
            which flips the lightness of every colour given in hex, and of
            white. Each is drawn with CSS `light-dark()`, which follows the
            theme's light and dark schemes where the theme sets the CSS
            `color-scheme`, as Zensical does. Text on a fill with a
            counterpart is drawn in the page's text colour. Needs
            `theme_colours`.

    Returns:
        A `<div class="dotdoc-graph">` holding a short stylesheet, the
        optional buttons, and the SVG with its overlays, with no blank lines, so
        a Markdown page can hold it as one raw HTML block.

    Raises:
        ValueError: If Graphviz drew an SVG without the layout the overlays are
            positioned from, or if `dark` is given without `theme_colours`.

    Examples:
        In a markdown-exec block in a documentation page:

        ```python
        drawing = graphviz.Digraph()
        drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
        print(graph_html(drawing))
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
    if dark is not None and not theme_colours:
        raise ValueError("`dark` needs `theme_colours`.")
    if theme_colours:
        svg = _theme_colours(svg, dark)
    _, _, view_width, view_height = _view_box(svg)
    size = f"--dotdoc-width:{width}pt;" if width is not None else ""
    size += f"--dotdoc-ratio:{view_width / view_height:.4f}"
    css = _CSS + (_CONTROLS_CSS if controls else "")
    return "".join(
        [
            f'<div class="dotdoc-graph"{_CLOSE_ON_ESCAPE if controls else ""}>',
            f"<style>{css}</style>",
            _CONTROLS if controls else "",
            '<div class="dotdoc-scroll">',
            f'<div class="dotdoc-drawing" style="{size}">',
            svg,
            *overlays,
            "</div></div></div>",
        ]
    )
