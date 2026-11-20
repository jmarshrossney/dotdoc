from dotdoc import api_autoref, summary


def test_api_autoref_is_the_dotted_path():
    assert api_autoref(summary) == "autoref:dotdoc.functions.summary"


class TestSummary:
    def test_none_without_a_docstring(self):
        def f():
            pass

        assert summary(f) is None
