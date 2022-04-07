import re
from base64 import b64decode
from io import BytesIO
from typing import Any, Dict, List, NamedTuple, Optional, Text, Union

import httpx
from httpx import HTTPStatusError
from pytest import fixture, raises

from typefit import api
from typefit import httpx_models as hm

from .httpbin_utils import HttpBin, find_free_port, wait_for_port


class DataUrl:
    """
    Decodes a Base64 encoded data URL
    """

    exp = re.compile(r"data:(?P<mime>[^;]+);base64,(?P<content>.*)")

    def __init__(self, url: Text):
        m = self.exp.match(url)

        if not m:
            raise ValueError

        self.mime = m.group("mime")
        self.content = b64decode(m.group("content").encode())


HttpArg = Union[Text, List[Text]]
HttpArgs = Dict[Text, HttpArg]
HttpHeaders = Dict[Text, Text]
HttpFiles = Dict[Text, DataUrl]


class HttpGet(NamedTuple):
    args: HttpArgs
    headers: HttpHeaders
    origin: Text
    url: Text


class HttpPost(NamedTuple):
    args: HttpArgs
    data: Text
    files: HttpFiles
    form: HttpArgs
    headers: HttpHeaders
    json: Any
    origin: Text
    url: Text


class HttpCookies(NamedTuple):
    cookies: Dict[Text, Text]


class HttpAuth(NamedTuple):
    authenticated: bool
    user: Text


@fixture(name="bin_url", scope="module")
def make_bin_url():
    port = find_free_port()
    hb = HttpBin(port)
    hb.run()

    try:
        wait_for_port(port, "127.0.0.1")
        yield f"http://127.0.0.1:{port}/"
    finally:
        hb.stop()


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

        @api.get("get", params={"value": "42"})
        def get(self) -> HttpGet:
            pass

    get = Bin().get()
    assert get.args["value"] == "42"


def test_get_params_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("get", params=lambda value: {"value": value})
        def get(self, value: int) -> HttpGet:
            pass

    get = Bin().get(42)
    assert get.args["value"] == "42"


def test_get_cookies_static(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def cookies(self) -> Optional[hm.CookieTypes]:
            return {"answer": "nope", "foo": "bar"}

        @api.get("cookies", cookies={"answer": "42"})
        def test_cookies(self) -> HttpCookies:
            pass

    cookies = Bin().test_cookies()
    assert cookies.cookies["answer"] == "42"
    assert cookies.cookies["foo"] == "bar"


def test_get_cookies_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("cookies", cookies=lambda answer: {"answer": answer})
        def test_cookies(self, answer: Text) -> HttpCookies:
            pass

    cookies = Bin().test_cookies("42")
    assert cookies.cookies["answer"] == "42"


def test_get_auth_static(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def auth(self) -> Optional[hm.AuthTypes]:
            return "foo", "bar"

        @api.get("basic-auth/{user}/{password}")
        def test_auth(self, user: Text, password: Text) -> HttpAuth:
            pass

    auth = Bin().test_auth("foo", "bar")
    assert auth.authenticated
    assert auth.user == "foo"


def test_get_auth_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get(
            "basic-auth/{user}/{password}", auth=lambda user, password: (user, password)
        )
        def test_auth(self, user: Text, password: Text) -> HttpAuth:
            pass

    auth = Bin().test_auth("foo", "bar")
    assert auth.authenticated
    assert auth.user == "foo"


def test_allow_redirect_static(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("redirect/1")
        def redirect(self) -> HttpGet:
            pass

    redirect = Bin().redirect()
    assert redirect.url.endswith("/get")


def test_allow_redirect_parametric(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.get("redirect/1", follow_redirects=lambda: False)
        def redirect(self) -> HttpGet:
            pass

    with raises(HTTPStatusError):
        Bin().redirect()


def test_post_data_form(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def data(self):
            return {"foo": ["1", "2"], "bar": "baz"}

        @api.post("post", data=data)
        def post(self) -> HttpPost:
            pass

    post = Bin().post()

    assert post.form["foo"] == ["1", "2"]
    assert post.form["bar"] == "baz"


def test_post_data_raw(bin_url):
    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def data(self):
            return "abc"

        @api.post("post", data=data)
        def post(self) -> HttpPost:
            pass

    post = Bin().post()

    assert post.data == "abc"


def test_post_files(bin_url):
    pixel = (
        b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff"
        b"\xff\xff!\xf9\x04\x01\x00\x00\x01\x00,\x00\x00\x00"
        b"\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
    )

    class Bin(api.SyncClient):
        BASE_URL = bin_url

        @api.post(
            "post", files=lambda: {"pixel": ("pixel.gif", BytesIO(pixel), "image/gif")}
        )
        def post(self) -> HttpPost:
            pass

    post = Bin().post()

    assert post.files["pixel"].mime == "image/gif"
    assert post.files["pixel"].content == pixel


def test_post_json(bin_url):
    data = {"foo": "bar", "yoo": [{"foo": 1}, {"bar": False}]}

    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def json(self):
            return data

        @api.post("post", json=json)
        def post(self) -> HttpPost:
            pass

    post = Bin().post()

    assert post.json == data


def test_put_json(bin_url):
    data = {"put": True}

    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def json(self):
            return data

        @api.put("put", json=json)
        def put(self) -> HttpPost:
            pass

    put = Bin().put()

    assert put.json == data


def test_patch_json(bin_url):
    data = {"patch": True}

    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def json(self):
            return data

        @api.patch("patch", json=json)
        def patch(self) -> HttpPost:
            pass

    patch = Bin().patch()

    assert patch.json == data
