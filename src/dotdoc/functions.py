"""Node attributes for Python functions, with or without Hamilton.

`api_autoref` links a node to a function's API entry, and `summary` gives the
first paragraph of its docstring, for a tooltip:

```python
drawing.node("split", URL=api_autoref(split), tooltip=summary(split))
```
"""

import inspect
from collections.abc import Callable

from .html import autoref

__all__ = ["api_autoref", "summary"]


def api_autoref(function: Callable) -> str:
    """Link a function to its mkdocstrings entry, wherever that is in the site.

    The identifier is the dotted path of the function where it is defined,
    `function.__module__` then `function.__qualname__`, which is where
    mkdocstrings registers it when that module is documented. See `autoref`.

    Args:
        function: The function to link to.

    Returns:
        A `URL` for `graph_html` to write as an `<autoref>` element.

    Examples:
        >>> from dotdoc import graph_html
        >>> api_autoref(graph_html)
        'autoref:dotdoc.html.graph_html'
    """
    return autoref(f"{function.__module__}.{function.__qualname__}")


def summary(function: Callable) -> str | None:
    """Return the first paragraph of a function's docstring, as plain text.

    The paragraph is put on one line and backticks are dropped, since a tooltip
    shows them literally.

    Args:
        function: The function whose docstring to read.

    Returns:
        The summary, or `None` if the function has no docstring.

    Examples:
        >>> def f():
        ...     '''Add one to `x`,
        ...     then double it.
        ...
        ...     More detail.
        ...     '''
        >>> summary(f)
        'Add one to x, then double it.'
    """
    doc = inspect.getdoc(function)
    if not doc:
        return None
    return " ".join(doc.split("\n\n", 1)[0].split()).replace("`", "")
