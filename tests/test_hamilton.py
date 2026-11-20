import pytest

from dotdoc.hamilton import (
    api_autoref,
    clean_legend,
    compose_styles,
    fill_by_tag,
    link_style,
    summary,
    tooltip_style,
)


def _fn(attrs, legend=None):
    return lambda *, node, node_class: (dict(attrs), node_class, legend)


def _node_line(source: str, name: str) -> str:
    return next(
        line for line in source.splitlines() if line.strip().startswith(f"{name} [")
    )


class TestComposeStyles:
    def test_later_attributes_win(self):
        composed = compose_styles(
            _fn({"fillcolor": "red", "color": "blue"}), _fn({"fillcolor": "green"})
        )
        style, base, legend = composed(node=None, node_class="function")
        assert style == {"fillcolor": "green", "color": "blue"}
        assert (base, legend) == ("function", None)

    def test_last_named_legend_wins(self):
        composed = compose_styles(
            _fn({}, legend="7D"), _fn({}, legend="output"), _fn({})
        )
        _, _, legend = composed(node=None, node_class="function")
        assert legend == "output"

    def test_nothing_composed_is_a_no_op(self):
        assert compose_styles()(node=None, node_class="function") == (
            {},
            "function",
            None,
        )


class TestSummary:
    def test_none_without_a_docstring(self):
        def f():
            pass

        assert summary(f) is None


@pytest.fixture(scope="module")
def styled_source(driver, api_url) -> str:
    style = compose_styles(
        fill_by_tag("stage", {"prepare": "#d9ead3", "model": "#fde9c4"}),
        tooltip_style(driver),
        link_style(driver, api_url),
    )
    return clean_legend(
        driver.display_all_functions(custom_style_function=style)
    ).source


@pytest.mark.dot
class TestLinks:
    def test_function_node_links_to_its_function(self, styled_source):
        assert 'URL="api.html#split"' in _node_line(styled_source, "split")

    def test_field_nodes_are_not_linked(self, styled_source):
        assert "URL=" not in _node_line(styled_source, "left")
        assert "URL=" not in _node_line(styled_source, "right")

    def test_config_when_node_links_by_qualname(self, styled_source):
        assert 'URL="api.html#start__equilibrate"' in _node_line(styled_source, "start")

    def test_inputs_and_config_are_not_linked(self, styled_source):
        assert "URL=" not in _node_line(styled_source, "_split_inputs")
        assert "URL=" not in _node_line(styled_source, "method")

    def test_link_returning_none_draws_no_link(self, driver):
        links = link_style(driver, lambda fn: None if fn.__name__ == "split" else "x")
        source = driver.display_all_functions(custom_style_function=links).source
        assert "URL=" not in _node_line(source, "split")
        assert "URL=x" in _node_line(source, "undocumented")


@pytest.mark.dot
class TestTooltips:
    def test_tooltip_is_the_first_docstring_paragraph_without_backticks(
        self, styled_source
    ):
        assert 'tooltip="Split the whole in two."' in _node_line(styled_source, "split")

    def test_backslashes_are_escaped(self, styled_source):
        """A `\\n` in a docstring is text, not a Graphviz line break."""
        line = _node_line(styled_source, "start")
        assert r'tooltip="Spin up to equilibrium, with a literal \\n in it."' in line

    def test_undocumented_and_field_nodes_get_none(self, styled_source):
        assert "tooltip=" not in _node_line(styled_source, "undocumented")
        assert "tooltip=" not in _node_line(styled_source, "left")

    def test_tooltip_function_is_a_parameter(self, driver):
        tips = tooltip_style(driver, lambda fn: fn.__name__.upper())
        source = driver.display_all_functions(custom_style_function=tips).source
        assert "tooltip=UNDOCUMENTED" in _node_line(source, "undocumented")


@pytest.mark.dot
class TestFillByTag:
    def test_tagged_nodes_are_filled(self, styled_source):
        assert 'fillcolor="#fde9c4"' in _node_line(styled_source, "start")
        assert 'fillcolor="#d9ead3"' in _node_line(styled_source, "left")

    def test_untagged_nodes_keep_hamilton_fill(self, styled_source):
        assert "#fde9c4" not in _node_line(styled_source, "undocumented")
        assert "#d9ead3" not in _node_line(styled_source, "undocumented")

    def test_each_value_gets_a_legend_entry(self, styled_source):
        legend = styled_source.split("cluster__legend", 1)[1]
        assert 'prepare [fillcolor="#d9ead3"' in legend
        assert 'model [fillcolor="#fde9c4"' in legend

    def test_unlisted_value_is_left_alone(self):
        style = fill_by_tag("stage", {"model": "red"})
        node = type("Node", (), {"tags": {"stage": "other"}})()
        assert style(node=node, node_class="function") == ({}, "function", None)


@pytest.mark.dot
class TestCleanLegend:
    def test_legend_entries_carry_no_links_or_tooltips(self, styled_source):
        legend = styled_source.split("cluster__legend", 1)[1]
        assert "URL=" not in legend
        assert "tooltip=" not in legend

    def test_nodes_outside_the_legend_keep_theirs(self, styled_source):
        before = styled_source.split("cluster__legend", 1)[0]
        assert "URL=" in before
        assert "tooltip=" in before

    def test_without_a_legend_nothing_changes(self, driver, api_url):
        links = link_style(driver, api_url)
        digraph = driver.display_all_functions(
            custom_style_function=links, show_legend=False
        )
        body = list(digraph.body)
        assert clean_legend(digraph).body == body


def test_api_autoref_is_the_dotted_path():
    assert api_autoref(summary) == "autoref:dotdoc.hamilton.summary"


@pytest.mark.dot
def test_link_style_defaults_to_api_autoref(driver):
    source = driver.display_all_functions(
        custom_style_function=link_style(driver)
    ).source
    assert 'URL="autoref:dotdoc_test_nodes.split"' in _node_line(source, "split")
