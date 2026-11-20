import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Example

    This page is a [marimo](https://marimo.io/) notebook, exported with its outputs by [`marimo-md-export`](https://github.com/jmarshrossney/marimo-md-export).
    Each drawing on it is the output of a cell, written into the page as HTML by [`graph_html`][dotdoc.html.graph_html].

    Hover over a node's name to preview its documentation, and click it to go there.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Any Graphviz drawing

    Giving a node a `URL` attribute makes its name a link.
    This drawing shows how dotdoc's functions fit together when drawing a Hamilton DAG, and links each function to its entry in the [API reference](api.md).
    Each `URL` is made by [`autoref`][dotdoc.html.autoref] from the function's dotted path, and the documentation build writes the link, so it works whatever the site's URL style.
    """)
    return


@app.cell
def _(autoref, graph_html, graphviz, mo):
    def api(name):
        return autoref(f"dotdoc.{name}")

    workflow = graphviz.Digraph(
        graph_attr={"rankdir": "LR"},
        node_attr={"fontname": "Helvetica", "shape": "box", "style": "rounded"},
    )
    for name in ("link_style", "tooltip_style", "fill_by_tag"):
        workflow.node(name, URL=api(f"hamilton.{name}"))
        workflow.edge(name, "compose_styles")
    workflow.node("compose_styles", URL=api("hamilton.compose_styles"))
    workflow.node("display", "Driver.display_all_functions", shape="ellipse")
    workflow.node("clean_legend", URL=api("hamilton.clean_legend"))
    workflow.node("graph_html", URL=api("html.graph_html"))
    workflow.node("page", "documentation page", shape="note", style="")
    workflow.edges(
        [
            ("compose_styles", "display"),
            ("display", "clean_legend"),
            ("clean_legend", "graph_html"),
            ("graph_html", "page"),
        ]
    )

    mo.Html(graph_html(workflow))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A Hamilton pipeline

    [`dotdoc.hamilton`](api.md#dotdoc.hamilton) builds those attributes for the nodes of an [Apache Hamilton](https://hamilton.apache.org/) DAG from the functions that define them.
    The pipeline here is the module `weather`, which turns a day of hourly temperatures into a summary:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # `marimo check` reads every file under examples/ as a notebook, so the
    # modules the notebooks import live in examples_lib/.
    import importlib
    import sys

    sys.path.insert(0, str(mo.notebook_dir().parent / "examples_lib"))
    weather = importlib.import_module("weather")
    return (weather,)


@app.cell
def _(weather):
    from hamilton import driver

    dr = driver.Builder().with_modules(weather).build()
    dr.execute(["summary"], inputs={"hourly": [4.2, 3.9, None, 3.1, 99.0, 5.6, 8.4]})
    return (dr,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    The drawing below composes three style functions:

    - `link_style` links each node to the mkdocstrings entry for its function, which for `weather` is at the end of this page;
    - `tooltip_style` shows the first paragraph of the function's docstring on hover, for when the preview is not to hand;
    - `fill_by_tag` fills each node by its `stage` tag, with an entry in the legend.

    Hamilton draws each legend entry with the style of the last node that named it, links and tooltips included, so `clean_legend` strips those from the legend.
    `fullscreen=True` adds a button that shows the drawing full screen.
    """)
    return


@app.cell
def _(
    clean_legend,
    compose_styles,
    dr,
    fill_by_tag,
    graph_html,
    link_style,
    mo,
    tooltip_style,
):
    style = compose_styles(
        fill_by_tag(
            "stage",
            {
                "read": "#d6e4f0",
                "check": "#d9ead3",
                "derive": "#fde9c4",
                "report": "#e4dcef",
            },
        ),
        tooltip_style(dr),
        link_style(dr),
    )
    pipeline = clean_legend(dr.display_all_functions(custom_style_function=style))

    mo.Html(graph_html(pipeline, fullscreen=True))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    The field nodes `low` and `high`, which `@extract_fields` makes from `temperature_range`, share its function, so only `temperature_range` is linked.
    Inputs such as `hourly` and `limit` have no function of their own and are not linked either.

    ## The pipeline's functions

    The documentation of `weather`, which the drawing links to.

    ::: weather
        options:
          show_root_heading: false
    """)
    return


@app.cell
def _():
    import graphviz
    import marimo as mo

    from dotdoc import autoref, graph_html
    from dotdoc.hamilton import (
        clean_legend,
        compose_styles,
        fill_by_tag,
        link_style,
        tooltip_style,
    )

    return (
        autoref,
        clean_legend,
        compose_styles,
        fill_by_tag,
        graph_html,
        graphviz,
        link_style,
        mo,
        tooltip_style,
    )


if __name__ == "__main__":
    app.run()
