# How it works

Graphviz lays out and draws the picture, Zensical (or MkDocs with mkdocs-autorefs) resolves links and shows previews, and dotdoc joins the two.
This page goes through what dotdoc does, step by step.

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

`graph_html` returns a single `<div>` holding a short stylesheet, the optional full-screen button, and the SVG with its overlays:

```html
<div class="dotdoc-graph">
  <style>...</style>
  <div class="dotdoc-drawing" style="position:relative;...">
    <svg>...</svg>
    <autoref identifier="dotdoc.html.graph_html" aria-label="graph_html" style="position:absolute;..." data-preview=""></autoref>
  </div>
</div>
```

It has no blank lines, so Markdown passes it through as one block of raw HTML.
A notebook cell outputs it, the notebook's export writes it into the page, and the documentation build resolves the `<autoref>` elements.
The overlays have to be in the page when it loads for the theme to find them, which is why the fragment is written into the page rather than added by a script.

The full-screen button is a single inline `onclick` handler, with the button's label swapped by CSS, so it needs no JavaScript file.

## Hamilton drawings

Hamilton's display methods take one style function, called for every node.
dotdoc's helpers each build one, and [`compose_styles`][dotdoc.hamilton.compose_styles] combines them:

- [`link_style`][dotdoc.hamilton.link_style] sets each node's `URL`, as in step 1;
- [`tooltip_style`][dotdoc.hamilton.tooltip_style] sets each node's tooltip to the [`summary`][dotdoc.hamilton.summary] of its function's docstring;
- [`fill_by_tag`][dotdoc.hamilton.fill_by_tag] colours each node by a tag and names a legend entry after it.

Hamilton draws each legend entry in the style of the last node that named it, links and tooltips included, so [`clean_legend`][dotdoc.hamilton.clean_legend] removes those from the legend before the drawing goes to `graph_html`.
