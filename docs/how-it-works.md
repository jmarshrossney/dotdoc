# How it works

Graphviz lays out and draws the picture, Zensical (or MkDocs with mkdocs-autorefs) resolves links and shows previews, and dotdoc joins the two.
This page goes through what dotdoc does, step by step.

The drawing below is made by dotdoc, from the code in its "Source" tab, when the documentation is built.
Hover over a node's name to preview what it links to, and click the name to go there: functions link to the API reference, and the steps dotdoc takes inside `graph_html` link to their section of this page.
Grey nodes are done by Graphviz or the documentation build.

```python exec="on" html="1" source="tabbed-right" result="html"
import graphviz

from dotdoc import autoref, graph_html


def api(name):
    return autoref(f"dotdoc.{name}")


drawing = graphviz.Digraph(
    graph_attr={"rankdir": "TB", "nodesep": "0.3"},
    node_attr={"fontname": "Helvetica", "fontsize": "12", "shape": "box"},
)
dotdoc_node = {"style": "rounded,filled", "fillcolor": "#e7eef7"}
other_node = {"style": "rounded,filled", "fillcolor": "#eeeeee", "color": "#999999"}

drawing.node(
    "autoref", "autoref\nidentifier as URL", URL=api("html.autoref"), **dotdoc_node
)
drawing.node(
    "link_style",
    "link_style\nURL for each Hamilton node",
    URL=api("hamilton.link_style"),
    **dotdoc_node,
)
drawing.node("graph_html", URL=api("html.graph_html"), **dotdoc_node)
drawing.node("svg", "SVG", **other_node)
drawing.node("layout", "JSON layout", **other_node)
drawing.node(
    "preview_overlay", "PREVIEW_OVERLAY", URL=api("html.PREVIEW_OVERLAY"), **dotdoc_node
)
drawing.node(
    "overlays",
    "overlays\none link per node name",
    URL="#3-an-invisible-link-is-laid-over-each-nodes-name",
    **dotdoc_node,
)
drawing.node(
    "unlinked",
    "unlinked SVG\ntooltips kept",
    URL="#4-the-links-inside-the-svg-are-removed",
    **dotdoc_node,
)
drawing.node(
    "fragment",
    "HTML fragment",
    URL="#5-everything-is-returned-as-one-piece-of-html",
    **dotdoc_node,
)
drawing.node("build", "documentation build\nresolves autorefs", **other_node)
drawing.node("theme", "theme\npreviews on hover", **other_node)

drawing.edges(
    [
        ("autoref", "graph_html"),
        ("link_style", "graph_html"),
        ("graph_html", "svg"),
        ("graph_html", "layout"),
        ("layout", "overlays"),
        ("preview_overlay", "overlays"),
        ("svg", "unlinked"),
        ("overlays", "fragment"),
        ("unlinked", "fragment"),
        ("fragment", "build"),
        ("build", "theme"),
    ]
)

print(graph_html(drawing, controls=True))
```

## 1. Each node is given a target

A node is linked by giving it a Graphviz `URL` attribute.
That is either an ordinary URL, written into the page as it is, or an identifier for the documentation build to resolve, made with [`autoref`][dotdoc.html.autoref]:

```python
drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
```

For a Hamilton DAG, [`link_style`][dotdoc.hamilton.link_style] sets the `URL` of every node that a function defines, by default to that function's identifier, through [`api_autoref`][dotdoc.hamilton.api_autoref].

## 2. Graphviz draws the picture, and says where everything is

[`graph_html`][dotdoc.html.graph_html] asks Graphviz for two renderings of the same drawing:

- the SVG, which is the picture that goes into the page;
- the JSON layout, which gives the position, size and text of everything in the picture.

From the layout, dotdoc finds the box around each linked node's name, taken to be the first line of its label.

## 3. An invisible link is laid over each node's name

For each linked node, dotdoc adds an empty, absolutely positioned HTML link on top of the SVG, exactly over the node's name.
Its position and size are written as percentages of the picture, so it stays in place when the picture scales to fit the page.

The overlay is an ordinary HTML link, so:

- the theme previews its target on hover, which it does not do for links inside an SVG;
- the keyboard and screen readers reach it, labelled with the node's name.

For an ordinary URL the overlay is `<a href="...">`.
For an identifier it is `<autoref identifier="...">`, which the documentation build replaces with a link to the identifier's entry, relative to the page and whatever the site's URL style.
Either way it carries the attributes given by `overlay`, by default [`PREVIEW_OVERLAY`][dotdoc.html.PREVIEW_OVERLAY], which turns on previews.

## 4. The links inside the SVG are removed

Graphviz has already made each linked node a link inside the SVG.
dotdoc removes those links, keeping the node's tooltip, so that only the name, under its overlay, is a link.
Following a link is then the same gesture as previewing it, and the page avoids SVG links that stop a theme previewing it.

Each linked node's name is underlined, whatever the theme does to links, to show where to click.

## 5. Everything is returned as one piece of HTML

`graph_html` returns a single `<div>` holding a short stylesheet, the optional buttons, and the SVG with its overlays:

```html
<div class="dotdoc-graph">
  <style>...</style>
  <div class="dotdoc-scroll">
    <div class="dotdoc-drawing" style="--dotdoc-width:...;--dotdoc-ratio:...">
      <svg>...</svg>
      <autoref identifier="dotdoc.html.graph_html" aria-label="graph_html" style="position:absolute;..." data-preview=""></autoref>
    </div>
  </div>
</div>
```

It has no blank lines, so Markdown passes it through as one block of raw HTML.
A notebook cell outputs it, the notebook's export writes it into the page, and the documentation build resolves the `<autoref>` elements.
The overlays have to be in the page when it loads for the theme to find them, which is why the fragment is written into the page rather than added by a script.

With `controls=True`, buttons above the drawing zoom it in and out and expand it to cover the window.
Zooming scales the drawing and its overlays together, inside an area that scrolls, so links and previews work at any size.
Each button is a single inline `onclick` handler, so they need no JavaScript file.

## Hamilton drawings

Hamilton's display methods take one style function, called for every node.
dotdoc's helpers each build one, and [`compose_styles`][dotdoc.hamilton.compose_styles] combines them:

- [`link_style`][dotdoc.hamilton.link_style] sets each node's `URL`, as in step 1;
- [`tooltip_style`][dotdoc.hamilton.tooltip_style] sets each node's tooltip to the [`summary`][dotdoc.hamilton.summary] of its function's docstring;
- [`fill_by_tag`][dotdoc.hamilton.fill_by_tag] colours each node by a tag and names a legend entry after it.

Hamilton draws each legend entry in the style of the last node that named it, links and tooltips included, so [`clean_legend`][dotdoc.hamilton.clean_legend] removes those from the legend before the drawing goes to `graph_html`.
