from typing import Any, Dict, List, NamedTuple, Optional, Text, Union

import httpx
import httpx.models as hm
from pytest import fixture
from typefit import api

HttpArg = Union[Text, List[Text]]
HttpArgs = Dict[Text, HttpArg]
HttpHeaders = Dict[Text, Text]


class HttpGet(NamedTuple):
    args: HttpArgs
    headers: HttpHeaders
    origin: Text
    url: Text


@fixture(name="bin_url")
def make_bin_url():
    return "https://httpbin.org/"


def test_get_simple(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("get?value={value}")
        def get(self, value: int) -> HttpGet:
            pass

    get = Bin().get(42)
    assert isinstance(get, HttpGet)
    assert get.args["value"] == "42"


def test_get_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get(lambda value: f"get?value={value}")
        def get(self, value: int) -> HttpGet:
            pass

    get = Bin().get(42)
    assert get.args["value"] == "42"


def test_get_headers_static(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def headers(self) -> Optional[hm.HeaderTypes]:
            return {"Foo": "Bar", "Answer": "nope"}

        @api.get("get", headers={"Answer": "42"})
        def get(self) -> HttpGet:
            pass

    get = Bin().get()
    assert get.headers["Foo"] == "Bar"
    assert get.headers["Answer"] == "42"


def test_get_headers_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("get", headers=lambda value: {"Answer": f"{value}"})
        def get(self, value: int) -> HttpGet:
            pass

    get = Bin().get(42)
    assert get.headers["Answer"] == "42"


def test_get_hint(bin_url):
    called = set()

    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("get", hint="foo")
        def get(self) -> HttpGet:
            pass

        def raise_errors(self, resp: httpx.Response, hint: Any) -> None:
            called.add("raise_errors")
            assert hint == "foo"
            return super().raise_errors(resp, hint)

        def decode(self, resp: httpx.Response, hint: Any) -> Any:
            called.add("decode")
            assert hint == "foo"
            return super().decode(resp, hint)

        def extract(self, data: Any, hint: Any) -> Any:
            called.add("extract")
            assert hint == "foo"
            return super().extract(data, hint)

    Bin().get()
    assert called == {"raise_errors", "decode", "extract"}


def test_get_params_static(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("get", params={'value': '42'})
        def get(self) -> HttpGet:
            pass

    get = Bin().get()
    assert get.args["value"] == "42"


def test_get_params_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("get", params=lambda value: {'value': value})
        def get(self, value: int) -> HttpGet:
            pass

    get = Bin().get(42)
    assert get.args["value"] == "42"
