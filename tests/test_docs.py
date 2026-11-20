"""Run the code blocks the documentation build executes.

markdown-exec writes a traceback into the page when a block raises, and the
build still passes, so this is the gate.
"""

import contextlib
import io
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.dot

_DOCS = Path(__file__).parent.parent / "docs"
_BLOCK_RE = re.compile(
    r'^```python exec="on"[^\n]*\n(.*?)^```', re.MULTILINE | re.DOTALL
)

_BLOCKS = [
    pytest.param(code, id=f"{path.name}-{i}")
    for path in sorted(_DOCS.glob("**/*.md"))
    for i, code in enumerate(_BLOCK_RE.findall(path.read_text()))
]


def test_there_are_blocks():
    assert _BLOCKS


@pytest.mark.parametrize("code", _BLOCKS)
def test_block_runs(code):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(code, {"__name__": "__main__"})
    assert output.getvalue()
