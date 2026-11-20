"""A Hamilton dataflow that draws a Hamilton DAG with dotdoc.

Each step is named after the function it calls.
"""

from collections.abc import Callable

import graphviz
from hamilton.driver import Driver
from hamilton.function_modifiers import tag
from hamilton.graph_types import HamiltonNode

import dotdoc
import dotdoc.hamilton
from dotdoc.hamilton import StyleFunction


def _api_entry(node: HamiltonNode, step: Callable | None) -> str | None:
    """Link a step to the API entry of the dotdoc function it is named after."""
    for module in (dotdoc.hamilton, dotdoc):
        if step and (function := getattr(module, step.__name__, None)) is not None:
            return dotdoc.hamilton.api_autoref(function)
    return None


@tag(stage="styling")
def link_style(dr: Driver) -> StyleFunction:
    """Link each node to the dotdoc function its step calls."""
    return dotdoc.hamilton.link_style(dr, link=_api_entry)


@tag(stage="styling")
def tooltip_style(dr: Driver) -> StyleFunction:
    """Give each node its step's docstring as a tooltip."""
    return dotdoc.hamilton.tooltip_style(dr)


@tag(stage="styling")
def fill_by_tag(tag: str, colours: dict[str, str]) -> StyleFunction:
    """Fill each node by its stage."""
    return dotdoc.hamilton.fill_by_tag(tag, colours)


@tag(stage="styling")
def compose_styles(
    link_style: StyleFunction,
    tooltip_style: StyleFunction,
    fill_by_tag: StyleFunction,
) -> StyleFunction:
    """Combine the style functions into the one Hamilton takes."""
    return dotdoc.hamilton.compose_styles(fill_by_tag, tooltip_style, link_style)


@tag(stage="rendering")
def display_all_functions(
    dr: Driver, compose_styles: StyleFunction
) -> graphviz.Digraph:
    """Draw the DAG with Hamilton, top to bottom, each input once."""
    return dr.display_all_functions(
        custom_style_function=compose_styles, orient="TB", deduplicate_inputs=True
    )


@tag(stage="rendering")
def clean_legend(display_all_functions: graphviz.Digraph) -> graphviz.Digraph:
    """Drop the links and tooltips Hamilton copies into the legend."""
    return dotdoc.hamilton.clean_legend(display_all_functions)


@tag(stage="output")
def graph_html(clean_legend: graphviz.Digraph) -> str:
    """Render the drawing as HTML for the page."""
    return dotdoc.graph_html(clean_legend, controls=True, dark="auto")
