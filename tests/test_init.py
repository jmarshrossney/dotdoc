import pytest

from dotdoc import greet


def test_greet_default():
    assert greet() == "Hello, world!"


@pytest.mark.parametrize("name", ["reader", "dotdoc", ""])
def test_greet_name(name):
    assert greet(name) == f"Hello, {name}!"
