"""Make Graphviz drawings a navigable part of your documentation: nodes link to their API entries, with previews on hover.

This module is a placeholder. Replace it with your own — the point of the
placeholder is to give the project a real public API, so that the linter, the
type checker, the test suite and the API reference all have something to act on
from the first commit.
"""

__all__ = ["greet"]


def greet(name: str = "world") -> str:
    """Build a friendly greeting.

    Args:
        name: Who to greet.

    Returns:
        The greeting.

    Examples:
        >>> greet()
        'Hello, world!'
        >>> greet("dotdoc")
        'Hello, dotdoc!'
    """
    return f"Hello, {name}!"
