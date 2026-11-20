# 1. Link nodes through HTML overlays on their names

Status: proposed

## Context

`graph_html` puts a Graphviz drawing into a documentation page so that each node links to its documentation and the theme (Zensical, Material for MkDocs) previews the target on hover.
Graphviz turns a node's `URL` attribute into an SVG `<a xlink:href>` around the whole node.

Three findings constrain how the link can be made:

- Themes preview only HTML links that are in the page when it loads: an SVG link gets no preview.
- Zensical's preview code fails on any page holding an SVG `<a>` with a plain `href`, so previews *to* that page, from anywhere, silently stop working.
  Graphviz writes `xlink:href`, which is not affected, but resolving an `<autoref>` inside the SVG writes a plain `href`.
- A link that works whatever the site's URL style (`use_directory_urls` true or false) has to be written by the documentation build, through mkdocs-autorefs or Zensical's autorefs, not by dotdoc.

## Decision

1. **Each linked node's link is an HTML overlay, not the SVG.**
   `graph_html` lays an empty, absolutely positioned `<a href>` or `<autoref identifier>` over the node, positioned from Graphviz's JSON layout as percentages of the picture, and removes the node's link from the SVG, keeping its tooltip.
   The overlay is the node's only link, so it is exposed to the keyboard and screen readers and labelled with the node's name.
2. **Only the node's name is clickable, not the whole node.**
   The overlay covers the first line of the node's label, which is underlined; the rest of the node is not a link.

Edge and graph links are left to the SVG.

## Consequences

- Hovering and clicking happen on the same spot: what is previewed is what is followed, and the underline shows where that is.
- Previews work on nodes, and on the pages that hold drawings.
- `autoref` identifiers resolve in either URL style, and an unknown identifier is a build warning.
- No JavaScript is needed for links.
- A node's name must be the first line of its label, and a node with no text is covered whole.
- Clicking the rest of a node does nothing, which a reader used to Graphviz SVGs may not expect.
- `overlay=None` no longer removes the overlays, only their extra attributes, since the overlay is the link.
- Outside a documentation build, for example in the marimo editor, `autoref` links lead nowhere.
- The fragment must be written into the page source, not added by a script, for the theme to find the overlays.

## Alternatives considered

- **Keep the SVG link and add an overlay only for previews.**
  This was the design ported from catena.
  The whole node followed the link, but only the name previewed it, and `autoref` could not be used inside the SVG without breaking previews of the page.
- **Overlay on the name, and forward clicks on the node body to it with an inline `onclick`.**
  Implemented and tested in a browser, then dropped: it needed JavaScript in the fragment, and clicking a spot that shows no preview should not navigate.
- **Overlay the whole node.**
  The overlay would hide the SVG tooltip, and the preview would appear wherever the pointer crossed the node, which is noisy on a dense drawing.
