"""Run the code blocks the documentation build executes.

markdown-exec writes a traceback into the page when a block raises, and the
build still passes, so this is the gate.
"""

import contextlib
import io
import re
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.dot

_DOCS = Path(__file__).parent.parent / "docs"
_BLOCK_RE = re.compile(
    r'^(?P<indent>[ \t]*)```python exec="on"[^\n]*\n(?P<code>.*?)^(?P=indent)```',
    re.MULTILINE | re.DOTALL,
)


def _blocks(text):
    """Executed blocks in `text`, including those indented inside admonitions."""
    return [textwrap.dedent(m["code"]) for m in _BLOCK_RE.finditer(text)]


_BLOCKS = [
    pytest.param(code, id=f"{path.name}-{i}")
    for path in sorted(_DOCS.glob("**/*.md"))
    for i, code in enumerate(_blocks(path.read_text()))
]


def test_there_are_blocks():
    assert _BLOCKS


@pytest.mark.parametrize("code", _BLOCKS)
def test_block_runs(code):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(code, {"__name__": "__main__"})
    assert output.getvalue()


def test_readme_shows_the_home_page_example():
    """The README's images are drawn from this code by `just readme-images`."""
    root = _DOCS.parent
    (example,) = _blocks((root / "docs" / "index.md").read_text())
    assert f"```python\n{example}```" in (root / "README.md").read_text()
