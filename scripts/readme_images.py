"""Draw the README's images from the example on the documentation's home page.

GitHub does not show inline SVG in a README, so the README shows these
instead, one for each colour scheme, without links or previews.
"""

import contextlib
import io
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXAMPLE_RE = re.compile(
    r'^```python exec="on"[^\n]*\n(.*?)^```', re.MULTILINE | re.DOTALL
)

COLOURS = {"light": "#1f2328", "dark": "#e6edf3"}


def main() -> None:
    """Write `.github/assets/example-{light,dark}.svg`."""
    match = EXAMPLE_RE.search((ROOT / "docs" / "index.md").read_text())
    if match is None:
        raise SystemExit("no example in docs/index.md")
    namespace: dict = {}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(match[1], namespace)
    for scheme, colour in COLOURS.items():
        drawing = namespace["drawing"].copy()
        drawing.graph_attr["bgcolor"] = "transparent"
        drawing.node_attr.update(color=colour, fontcolor=colour)
        drawing.edge_attr.update(color=colour)
        drawing.body = [
            re.sub(r'URL="[^"]*" ?', "", line).replace(" []", "")
            for line in drawing.body
        ]
        path = ROOT / ".github" / "assets" / f"example-{scheme}.svg"
        path.write_text(drawing.pipe(format="svg", encoding="utf-8"))


if __name__ == "__main__":
    main()
