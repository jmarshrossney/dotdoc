import shutil
import sys
import textwrap
import types

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "dot: needs the Graphviz `dot` program")


def pytest_collection_modifyitems(config, items):
    if shutil.which("dot"):
        return
    skip = pytest.mark.skip(reason="the Graphviz `dot` program is not installed")
    for item in items:
        if "dot" in item.keywords:
            item.add_marker(skip)


_NODES = '''\
from typing import TypedDict

from hamilton.function_modifiers import config, extract_fields, tag


class Parts(TypedDict):
    left: float
    right: float


@tag(stage="prepare")
@extract_fields({"left": float, "right": float})
def split(whole: float) -> Parts:
    """Split the `whole` in two.

    Longer description that the tooltip leaves out.
    """
    return {"left": whole / 2, "right": whole / 2}


@tag(stage="model")
@config.when(method="equilibrate")
def start__equilibrate(left: float, rate: float = 1.0) -> float:
    """Spin up to equilibrium, with a literal \\\\n in it."""
    return left * rate


def undocumented(right: float) -> float:
    return right
'''


@pytest.fixture(scope="session")
def nodes_module():
    module = types.ModuleType("dotdoc_test_nodes")
    sys.modules[module.__name__] = module
    exec(textwrap.dedent(_NODES), module.__dict__)
    yield module
    del sys.modules[module.__name__]


@pytest.fixture(scope="session")
def driver(nodes_module):
    from hamilton import driver

    return (
        driver.Builder()
        .with_modules(nodes_module)
        .with_config({"method": "equilibrate"})
        .build()
    )


@pytest.fixture(scope="session")
def api_url():
    return lambda node, fn: fn and f"api.html#{fn.__qualname__}"
