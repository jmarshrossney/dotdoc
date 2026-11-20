import functools

import pytest

from dotdoc import api_autoref, summary


def test_api_autoref_is_the_dotted_path():
    assert api_autoref(summary) == "autoref:dotdoc.functions.summary"


class TestSummary:
    def test_none_without_a_docstring(self):
        def f():
            pass

        assert summary(f) is None


class TestApiAutorefRejects:
    @pytest.mark.parametrize(
        "function",
        [functools.partial(print), lambda: 0],
        ids=["partial", "lambda"],
    )
    def test_callables_without_an_api_entry(self, function):
        with pytest.raises(TypeError, match="api_autoref needs"):
            api_autoref(function)

    def test_nested_function(self):
        def nested():
            pass

        with pytest.raises(TypeError, match="api_autoref needs"):
            api_autoref(nested)


def test_hamilton_reexports():
    hamilton = pytest.importorskip("dotdoc.hamilton")
    assert {"api_autoref", "summary"} <= set(hamilton.__all__)
    assert hamilton.api_autoref is api_autoref
    assert hamilton.summary is summary
