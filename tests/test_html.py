import re
import xml.etree.ElementTree as ET

import graphviz
import pytest

from dotdoc import AUTOREF_PREFIX, autoref, graph_html
from dotdoc.hamilton import link_style

pytestmark = pytest.mark.dot

_SVG = "{http://www.w3.org/2000/svg}"
_XLINK_HREF = "{http://www.w3.org/1999/xlink}href"


def _percent(style: str) -> dict[str, float]:
    return {k: float(v) for k, v in re.findall(r"(\w+):([-\d.]+)%", style)}


@pytest.fixture(scope="module")
def linked_digraph(driver, api_url):
    return driver.display_all_functions(
        custom_style_function=link_style(driver, api_url)
    )


@pytest.fixture(scope="module")
def fragment(linked_digraph) -> str:
    return graph_html(linked_digraph)


def _drawing(fragment: str) -> ET.Element:
    drawing = ET.fromstring(fragment).find(".//div[@class='dotdoc-drawing']")
    assert drawing is not None
    return drawing


def test_is_one_element_without_prolog_or_blank_lines(fragment):
    assert fragment.startswith('<div class="dotdoc-graph"')
    assert "<?xml" not in fragment
    assert "<!DOCTYPE" not in fragment
    assert "\n\n" not in fragment
    ET.fromstring(fragment)


def test_only_linked_node_names_are_underlined(fragment):
    style = ET.fromstring(fragment).find("style")
    assert style is not None
    assert style.text is not None
    assert "svg a{text-decoration:none;color:inherit}" in style.text
    assert "a.dotdoc-link text:first-of-type{text-decoration:underline}" in style.text
    svg = _drawing(fragment).find(f"{_SVG}svg")
    assert svg is not None
    linked = [a for a in svg.iter(f"{_SVG}a") if a.get("class") == "dotdoc-link"]
    assert len(linked) == 3


@pytest.mark.parametrize("controls", [False, True])
def test_no_square_brackets_outside_the_svg(linked_digraph, controls):
    """Markdown escapes square brackets, even inside raw HTML."""
    fragment = graph_html(linked_digraph, controls=controls)
    assert "[" not in fragment.split("<svg", 1)[0]


def test_svg_scales_to_fit(fragment):
    drawing = _drawing(fragment)
    svg = drawing.find(f"{_SVG}svg")
    assert svg is not None
    assert "width" not in svg.attrib
    assert "height" not in svg.attrib
    assert "width:100%" in svg.attrib["style"]
    assert re.search(r"--dotdoc-width:[\d.]+pt;", drawing.attrib["style"])
    _, _, width, height = map(float, svg.attrib["viewBox"].split())
    ratio = re.search(r"--dotdoc-ratio:([\d.]+)", drawing.attrib["style"])
    assert ratio is not None
    assert float(ratio[1]) == pytest.approx(width / height, rel=1e-3)


def test_one_overlay_per_linked_node(fragment):
    overlays = _drawing(fragment).findall("a")
    hrefs = sorted(a.attrib["href"] for a in overlays)
    assert hrefs == [
        "api.html#split",
        "api.html#start__equilibrate",
        "api.html#undocumented",
    ]
    for overlay in overlays:
        assert overlay.attrib["data-preview"] == ""
        # The overlay is the link, so it is not hidden from the keyboard or
        # screen readers, and it is named after the node.
        assert "aria-hidden" not in overlay.attrib
        assert "tabindex" not in overlay.attrib
    labels = sorted(a.attrib["aria-label"] for a in overlays)
    assert labels == ["split", "start: method", "undocumented"]


def test_node_bodies_are_not_links(fragment):
    """Only the name, under its overlay, is a link."""
    svg = _drawing(fragment).find(f"{_SVG}svg")
    assert svg is not None
    for link in svg.iter(f"{_SVG}a"):
        assert _XLINK_HREF not in link.attrib
        assert "href" not in link.attrib
        assert "onclick" not in link.attrib
    assert "<script" not in fragment


def test_edge_links_are_left_to_the_svg():
    drawing = graphviz.Digraph()
    drawing.node("a", URL="#a")
    drawing.edge("a", "b", URL="#edge")
    drawing_el = _drawing(graph_html(drawing))
    svg = drawing_el.find(f"{_SVG}svg")
    assert svg is not None
    hrefs = [a.get(_XLINK_HREF) for a in svg.iter(f"{_SVG}a")]
    assert hrefs.count("#edge") == 1
    assert "#a" not in hrefs
    assert [a.attrib["href"] for a in drawing_el.findall("a")] == ["#a"]


def test_overlay_covers_its_node_name(fragment):
    drawing = _drawing(fragment)
    svg = drawing.find(f"{_SVG}svg")
    assert svg is not None
    _, _, width, height = map(float, svg.attrib["viewBox"].split())
    graph = svg.find(f"{_SVG}g")
    assert graph is not None
    tx, ty = map(
        float,
        re.findall(r"translate\(([-\d.]+) ([-\d.]+)\)", graph.attrib["transform"])[0],
    )
    for overlay in drawing.findall("a"):
        link = next(
            a
            for a in svg.iter(f"{_SVG}a")
            if next(a.iter(f"{_SVG}text")).text == overlay.attrib["aria-label"]
        )
        outline = next(el for el in link if el.tag in (f"{_SVG}path", f"{_SVG}polygon"))
        coords = re.findall(
            r"([-\d.]+),([-\d.]+)",
            outline.attrib.get("d", "") or outline.attrib["points"],
        )
        xs = [(float(x) + tx) / width * 100 for x, _ in coords]
        ys = [(float(y) + ty) / height * 100 for _, y in coords]
        name = next(t for t in link.iter(f"{_SVG}text"))
        assert name.attrib["font-weight"] == "bold"
        name_x = (float(name.attrib["x"]) + tx) / width * 100
        baseline = (float(name.attrib["y"]) + ty) / height * 100
        box = _percent(overlay.attrib["style"])
        right, bottom = box["left"] + box["width"], box["top"] + box["height"]
        assert box["left"] == pytest.approx(name_x, abs=0.1)
        assert box["top"] < baseline < bottom
        assert min(xs) < box["left"] < right < max(xs)
        assert min(ys) < box["top"] < bottom < max(ys)


def test_overlay_attributes_are_a_parameter(linked_digraph):
    fragment = graph_html(linked_digraph, overlay={"data-kind": "node"})
    overlays = _drawing(fragment).findall("a")
    assert overlays
    assert all(a.attrib == a.attrib | {"data-kind": "node"} for a in overlays)
    assert "data-preview" not in fragment


def test_no_overlay_attributes(linked_digraph):
    overlays = _drawing(graph_html(linked_digraph, overlay=None)).findall("a")
    assert len(overlays) == 3
    assert all(set(a.attrib) == {"href", "aria-label", "style"} for a in overlays)


def test_no_controls_by_default(fragment):
    root = ET.fromstring(fragment)
    assert root.find(".//button") is None
    assert "onkeydown" not in root.attrib
    assert "dotdoc-expanded" not in fragment


def test_controls(linked_digraph):
    root = ET.fromstring(graph_html(linked_digraph, controls=True))
    expand, zoom_out, zoom_in = root.iter("button")
    assert "toggle('dotdoc-expanded')" in expand.attrib["onclick"]
    assert [span.text for span in expand] == ["Expand", "Close"]
    assert zoom_out.attrib["aria-label"] == "Zoom out"
    assert "Math.max(1,z/1.25)" in zoom_out.attrib["onclick"]
    assert zoom_in.attrib["aria-label"] == "Zoom in"
    assert "Math.min(8,z*1.25)" in zoom_in.attrib["onclick"]
    assert "Escape" in root.attrib["onkeydown"]
    style = root.find("style")
    assert style is not None
    assert style.text is not None
    assert ".dotdoc-graph.dotdoc-expanded{position:fixed" in style.text


def test_drawing_is_in_a_scroll_area(fragment):
    scroll = ET.fromstring(fragment).find("div")
    assert scroll is not None
    assert scroll.attrib["class"] == "dotdoc-scroll"
    assert [child.attrib["class"] for child in scroll] == ["dotdoc-drawing"]


@pytest.mark.parametrize("cls", [graphviz.Graph, graphviz.Digraph])
def test_any_graphviz_drawing_with_cycles(cls):
    drawing = cls()
    drawing.node("a", URL="#a")
    drawing.node("b", label="b\nsecond line", URL="#b", shape="box")
    drawing.node("c")
    drawing.edges(["ab", "bc", "ca"])
    overlays = _drawing(graph_html(drawing)).findall("a")
    assert sorted(a.attrib["href"] for a in overlays) == ["#a", "#b"]


def test_node_without_text_is_covered_whole():
    drawing = graphviz.Digraph()
    drawing.node("a", label="", URL="#a", shape="box", width="1", height="0.5")
    (overlay,) = _drawing(graph_html(drawing)).findall("a")
    box = _percent(overlay.attrib["style"])
    assert box["width"] == pytest.approx(100 * 72 / 80, abs=1)


@pytest.fixture(scope="module")
def autoref_fragment(driver) -> str:
    return graph_html(
        driver.display_all_functions(custom_style_function=link_style(driver))
    )


def test_autoref_prefix():
    assert autoref("a.b") == AUTOREF_PREFIX + "a.b"


def test_autoref_overlays_are_autoref_elements(autoref_fragment):
    assert "autoref:" not in autoref_fragment
    overlays = _drawing(autoref_fragment).findall("autoref")
    identifiers = sorted(o.attrib["identifier"] for o in overlays)
    assert identifiers == [
        "dotdoc_test_nodes.split",
        "dotdoc_test_nodes.start__equilibrate",
        "dotdoc_test_nodes.undocumented",
    ]
    for overlay in overlays:
        assert overlay.attrib["data-preview"] == ""
        assert "position:absolute" in overlay.attrib["style"]
    labels = sorted(o.attrib["aria-label"] for o in overlays)
    assert labels == ["split", "start: method", "undocumented"]


def test_unlinked_node_keeps_svg_tooltip():
    drawing = graphviz.Digraph()
    drawing.node("a", URL=autoref("pkg.a"), tooltip='say "hi" & <go>')
    link = next(ET.fromstring(graph_html(drawing)).iter(f"{_SVG}a"))
    assert link.attrib["class"] == "dotdoc-link"
    assert link.attrib["{http://www.w3.org/1999/xlink}title"] == 'say "hi" & <go>'


def test_plain_and_autoref_links_mix():
    drawing = graphviz.Digraph()
    drawing.node("a", URL=autoref("pkg.a"))
    drawing.node("b", URL="https://example.org/b")
    drawing.edge("a", "b")
    drawing_el = _drawing(graph_html(drawing))
    assert [o.attrib["identifier"] for o in drawing_el.findall("autoref")] == ["pkg.a"]
    assert [o.attrib["href"] for o in drawing_el.findall("a")] == [
        "https://example.org/b"
    ]


def _colours_drawing() -> graphviz.Digraph:
    drawing = graphviz.Digraph()
    drawing.node("filled", style="filled", fillcolor="#fde9c4")
    drawing.node("plain")
    drawing.node("red", color="red", fontcolor="red")
    cluster = graphviz.Digraph(name="cluster_group", graph_attr={"label": "group"})
    cluster.node("inside")
    drawing.subgraph(cluster)
    drawing.edge("filled", "plain", label="edge")
    drawing.edge("plain", "inside")
    return drawing


def _texts(svg: ET.Element) -> dict[str | None, str | None]:
    return {t.text: t.get("fill") for t in svg.iter(f"{_SVG}text")}


def test_theme_colours():
    svg = _drawing(graph_html(_colours_drawing())).find(f"{_SVG}svg")
    assert svg is not None
    # No background.
    assert not any(p.get("fill") == "white" for p in svg.iter(f"{_SVG}polygon"))
    # Default black follows the page; set colours are kept.
    strokes = {el.get("stroke") for el in svg.iter() if el.get("stroke")}
    assert "black" not in strokes
    assert {"currentColor", "red"} <= strokes
    assert "black" not in {el.get("fill") for el in svg.iter()}
    # Text on the page follows it; text on a fill keeps Graphviz's black.
    texts = _texts(svg)
    assert texts["plain"] == "currentColor"
    assert texts["edge"] == "currentColor"
    assert texts["group"] == "currentColor"
    assert texts["inside"] == "currentColor"
    assert texts["filled"] is None
    assert texts["red"] == "red"


def test_graphviz_colours():
    svg = _drawing(graph_html(_colours_drawing(), theme_colours=False)).find(
        f"{_SVG}svg"
    )
    assert svg is not None
    assert "currentColor" not in ET.tostring(svg, encoding="unicode")
    assert any(p.get("fill") == "white" for p in svg.iter(f"{_SVG}polygon"))
