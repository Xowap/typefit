from typefit.utils import UrlFormatter, loose_call


def test_loose_call():
    def foo(a):
        return a

    assert loose_call(foo, {"a": 1}) == 1
    assert loose_call(foo, {"a": 1, "b": 2}) == 1

    def bar(a, **kwargs):
        return a, kwargs

    assert loose_call(bar, {"a": 1}) == (1, {})
    assert loose_call(bar, {"a": 1, "b": 2}) == (1, {"b": 2})


def test_url_formatter():
    class Data:
        def __str__(self):
            return "str/"

        def __repr__(self):
            return "räpr/"

    f = UrlFormatter()

    assert f.format("{}/{}", "one", "two") == "one/two"
    assert f.format("{:+d}", 42) == "%2B42"
    assert f.format("{0!s} {0!r} {0!a}", Data()) == "str%2F r%C3%A4pr%2F r%5Cxe4pr%2F"
    assert f.format("{:>10}", "test") == "++++++test"
    assert f.format("{:f}", 3.141592653589793) == "3.141593"
    assert f.format("{:06.2f}", 3.141592653589793) == "003.14"
