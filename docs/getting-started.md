# Getting started

## Installation

Install from PyPI:

```sh
pip install dotdoc
```

Or, if you use [uv](https://docs.astral.sh/uv/), add it to a project:

```sh
uv add dotdoc
```

For drawings of Apache Hamilton DAGs, add the `hamilton` extra:

```sh
pip install "dotdoc[hamilton]"
```

Rendering needs Graphviz's `dot` program on the `PATH`, from your system's package manager (`apt install graphviz`, `brew install graphviz`).

## First steps

`graph_html` renders any Graphviz drawing as an HTML fragment.
A node with a `URL` attribute links there, and gets an invisible HTML link over its name that carries `data-preview`, so Zensical and Material for MkDocs preview the target on hover.

```python
import graphviz
from dotdoc import autoref, graph_html

drawing = graphviz.Digraph()
drawing.node("graph_html", URL=autoref("dotdoc.html.graph_html"))
html = graph_html(drawing, controls=True)
```

Write `html` into the page source, or return `mo.Html(html)` from a marimo notebook exported to the page.
The overlay links must be in the page when it loads, so do not add the fragment from a script.

## Linking to API entries

`autoref` names an mkdocstrings identifier rather than a URL.
The documentation build, through Zensical's autorefs or the mkdocs-autorefs plugin, writes the link relative to each page, so it works whether `use_directory_urls` is on or off.
An identifier the build cannot find is reported as a warning.
These links only work in a page those tools build; in the marimo editor, for instance, they lead nowhere.

A plain URL is written into the page as it is, so it must already be correct from the built page: `api.html#…` with `use_directory_urls = false`, `../api/#…` with it on.

## Hamilton DAGs

Compose `dotdoc.hamilton`'s style functions and pass them to any of the driver's display methods.
By default `link_style` links each node to the mkdocstrings entry of the function that defines it:

```python
from dotdoc.hamilton import clean_legend, compose_styles, link_style, tooltip_style

style = compose_styles(tooltip_style(dr), link_style(dr))
html = graph_html(clean_legend(dr.display_all_functions(custom_style_function=style)))
```

The [example](example.md) does both, and the [API reference](api.md) has the details.

## Previewing locally

Use `zensical serve` and open the address it prints.
With `use_directory_urls = false`, previews only work under the site's path from `site_url` (for example `/dotdoc/`, where the root redirects): not on un-prefixed URLs such as `/example.html`, and not when opening `site/*.html` as files.
With `use_directory_urls = true` they work wherever the site is served, except from files.

## Maths

KaTeX is wired up, so inline maths like $e^{i\pi} = -1$ and display maths

$$
\int_{-\infty}^{\infty} e^{-x^{2}} \, \mathrm{d}x = \sqrt{\pi}
$$

both render. This section exists so the docs build exercises the KaTeX
configuration; delete it (and see `zensical.toml`) if this package's
documentation has no maths in it.
