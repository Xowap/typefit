from functools import wraps
from inspect import signature
from typing import Any, Callable, Dict, List, Optional, Text, Type, Union
from urllib.parse import urljoin

import httpx

from . import httpx_models as hm
from .fitting import T, typefit
from .serialize import SaneSerializer
from .utils import UrlFormatter, callable_value

HeadersFactory = Callable[..., hm.HeaderTypes]
Headers = Union[None, hm.HeaderTypes, HeadersFactory]

PathFactory = Callable[..., Text]
Path = Union[PathFactory, Text]

ParamsFactory = Callable[..., hm.QueryParamTypes]
Params = Union[None, hm.QueryParamTypes, ParamsFactory]

CookiesFactory = Callable[..., hm.CookieTypes]
Cookies = Union[None, hm.CookieTypes, CookiesFactory]

AuthFactory = Callable[..., hm.AuthTypes]
Auth = Union[None, hm.AuthTypes, AuthFactory]

FollowRedirectsFactory = Callable[..., bool]
FollowRedirects = Union[None, bool, FollowRedirectsFactory]

DataFactory = Callable[..., hm.RequestData]
Data = Union[None, hm.RequestData, DataFactory]

FilesFactory = Callable[..., hm.RequestFiles]
Files = Union[None, hm.RequestFiles, FilesFactory]

JsonType = Union[Dict[Text, "JsonType"], List["JsonType"], int, float, bool, Text, None]
JsonFactory = Callable[..., hm.RequestFiles]
Json = Union[None, JsonType, JsonFactory]


OnResponse = Callable[[hm.Request, hm.Response], None]


def _make_decorator(
    method: Text,
    path: Path,
    data: Data = None,
    files: Files = None,
    json: Json = None,
    params: Params = None,
    headers: Headers = None,
    cookies: Cookies = None,
    auth: Auth = None,
    follow_redirects: FollowRedirects = None,
    hint: Any = None,
) -> Callable[[Callable], Callable]:
    """
    Generates a decorator that can be used for any kind of HTTP request.
    That's a bit messy but without it the GET/POST/etc decorators would share
    very duplicated code.
    """

    def decorator(func: Callable):
        sig = signature(func)

        if len(sig.parameters) == 0:
            raise TypeError("Decorated function doesn't have any arguments")

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Gets the signature from the decorated function and applies the
            arguments received from the call. If the arguments are no good then
            it will fail.

            Then uses the helper's get method in order to generate the actual
            request and arguments.

            The real method is never called.
            """

            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            self = next(iter(bound.arguments.values()))

            if not isinstance(self, SyncClient):
                raise TypeError(f"{self!r} is not a SyncClient")

            return self.helper.request(
                method=method,
                path=path,
                data=data,
                files=files,
                json=json,
                params=params,
                headers=headers,
                cookies=cookies,
                auth=auth,
                follow_redirects=follow_redirects,
                hint=hint,
                kwargs=bound.arguments,
                data_type=sig.return_annotation,
            )

        return wrapper

    return decorator


def get(
    path: Path,
    params: Params = None,
    headers: Headers = None,
    cookies: Cookies = None,
    auth: Auth = None,
    follow_redirects: FollowRedirects = None,
    hint: Any = None,
):
    """
    Generates an API method that GET the URL, based on provided parameters and
    method signature. The decorated method's code will never be called, only
    the generated method will be used.
    """

    return _make_decorator(
        "get",
        path=path,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        hint=hint,
    )


def post(
    path: Path,
    data: Data = None,
    files: Files = None,
    json: Json = None,
    params: Params = None,
    headers: Headers = None,
    cookies: Cookies = None,
    auth: Auth = None,
    follow_redirects: FollowRedirects = None,
    hint: Any = None,
):
    """
    Generates an API method that POST the URL, based on provided parameters and
    method signature. The decorated method's code will never be called, only
    the generated method will be used.
    """

    return _make_decorator(
        "post",
        path=path,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        hint=hint,
    )


def put(
    path: Path,
    data: Data = None,
    files: Files = None,
    json: Json = None,
    params: Params = None,
    headers: Headers = None,
    cookies: Cookies = None,
    auth: Auth = None,
    follow_redirects: FollowRedirects = None,
    hint: Any = None,
):
    """
    Generates an API method that PUT the URL, based on provided parameters and
    method signature. The decorated method's code will never be called, only
    the generated method will be used.
    """

    return _make_decorator(
        "put",
        path=path,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        hint=hint,
    )


def patch(
    path: Path,
    data: Data = None,
    files: Files = None,
    json: Json = None,
    params: Params = None,
    headers: Headers = None,
    cookies: Cookies = None,
    auth: Auth = None,
    follow_redirects: FollowRedirects = None,
    hint: Any = None,
):
    """
    Generates an API method that PATCH the URL, based on provided parameters
    and method signature. The decorated method's code will never be called,
    only the generated method will be used.
    """

    return _make_decorator(
        "patch",
        path=path,
        data=data,
        files=files,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        hint=hint,
    )


def delete(
    path: Path,
    data: Data = None,
    json: Json = None,
    params: Params = None,
    headers: Headers = None,
    cookies: Cookies = None,
    auth: Auth = None,
    follow_redirects: FollowRedirects = None,
    hint: Any = None,
):
    """
    Generates an API method that DELETE the URL, based on provided parameters
    and method signature. The decorated method's code will never be called,
    only the generated method will be used.
    """

    return _make_decorator(
        "delete",
        path=path,
        data=data,
        json=json,
        params=params,
        headers=headers,
        cookies=cookies,
        auth=auth,
        follow_redirects=follow_redirects,
        hint=hint,
    )


class _SyncClientHelper:
    """
    Effector for all requests and parameters generation. It's separated from
    the client itself for readability regarding what should or should not be
    overridden.
    """

    def __init__(self, client: "SyncClient"):
        self.client = client
        self.http = httpx.Client()
        self.on_response: Optional[OnResponse] = None

    def close(self):
        """
        Closes the underlying HTTP connection pool
        """

        self.http.close()

    def url(self, path: Path, kwargs: Dict[Text, Any]):
        """
        Generates the URL using urljoin in the client's BASE_URL and the
        provided path. The path could be a callable, if so it will be called
        using loose_call and the provided kwargs.
        """

        f = UrlFormatter()
        url = urljoin(self.client.BASE_URL, callable_value(path, kwargs))
        return f.format(url, **kwargs)

    def headers(self, extra: Headers, kwargs: Dict[Text, Any]) -> hm.Headers:
        """
        Generates the headers for this request. It will:

        1. Get the default headers as generated by the client's headers()
           method
        2. Use the specific extra headers specified via the decorator. Callable
           values will be called before being returned.

        All of that is merged and returned.
        """

        out = hm.Headers(self.client.headers())
        out.update(callable_value(extra, kwargs))

        return out

    def cookies(self, extra: Cookies, kwargs: Dict[Text, Any]) -> hm.Cookies:
        """
        Generates the cookies for this request. It will:

        1. Get the default cookies as generated by the client's cookies()
           method
        2. Use the specific extra cookies specified via the decorator. Callable
           values will be called before being returned.

        All of that is merged and returned.
        """

        out = hm.Cookies(self.client.cookies())
        out.update(callable_value(extra, kwargs))

        return out

    def auth(self, override: Auth, kwargs: Dict[Text, Any]) -> Auth:
        """
        If there is an override from the decorator then this prevails over the
        static auth provided by the client class but otherwise it will just use
        the output of the auth() method in the client.
        """

        ov = callable_value(override, kwargs)

        if ov:
            return ov

        return self.client.auth()

    def follow_redirects(
        self, override: FollowRedirects, kwargs: Dict[Text, Any]
    ) -> bool:
        """
        Checks if the decorator attempts an override (by returning a non-None
        value), otherwise stick to the client's value.
        """

        ov = callable_value(override, kwargs)

        if ov is not None:
            return ov

        return self.client.follow_redirects()

    def request(
        self,
        method: Text,
        kwargs: Dict[Text, Any],
        data_type: Type[T],
        path: Text,
        data: Data = None,
        files: Files = None,
        json: Json = None,
        headers: Headers = None,
        cookies: Cookies = None,
        auth: Auth = None,
        follow_redirects: FollowRedirects = None,
        params: Params = None,
        hint: Any = None,
    ) -> T:
        """
        This will generate a call to HTTPX depending on the provided overrides
        (in the arguments) and available default values as declared by the
        client. Arguments will be selected automatically depending on the
        method.
        """

        cookies = self.cookies(cookies, kwargs)
        old_cookies = None

        if cookies:
            old_cookies = self.http.cookies
            self.http.cookies = cookies

        request_args = dict(
            url=self.url(path, kwargs),
            headers=self.headers(headers, kwargs),
            params=callable_value(params, kwargs),
            auth=self.auth(auth, kwargs),
            follow_redirects=self.follow_redirects(follow_redirects, kwargs),
        )

        if method in {"post", "put", "patch"}:
            request_args.update(
                data=callable_value(data, kwargs),
                files=callable_value(files, kwargs),
                json=self.client.serialize(callable_value(json, kwargs)),
            )

        r: hm.Response = getattr(self.http, method)(**request_args)

        if self.on_response and r:
            self.on_response(r._request, r)

        self.client.raise_errors(r, hint)
        data = self.client.decode(r, hint)
        data = self.client.extract(data, hint)

        if cookies:
            self.http.cookies = old_cookies

        return self.client.typefit(data_type, data)


class SyncClient:
    """
    SyncClient base class. To create your own API client, inherit from this
    and generate your methods using the HTTP decorators found above.
    """

    BASE_URL = ""

    def __init__(self):
        self.helper = _SyncClientHelper(self)
        self.helper.on_response = self.on_response
        self.serialize = self.init_serialize()
        self.typefit = self.init_typefit()

    def init_typefit(self) -> Callable[[Type[T], Any], T]:
        """
        Uses :py:func:`~.typefit.typefit` by default, however you might want to
        configure things differently, like the logging of errors. If you want
        to do so, just override this method.
        """

        return typefit

    def init_serialize(self) -> Callable[[Any], Any]:
        """
        Everything going through the `json` parameter will be serialized using
        the serializer function returned by this method. By default this
        uses the :py:class:`~.typefit.serialize.SaneSerializer` class which
        is helpful in the general case. If you want something more specific,
        feel free to override this method.

        If you don't want your data to be tampered with at all, you can do
        something like

        >>> def init_serialize(self):
        >>>     return lambda x: x
        """

        return SaneSerializer().serialize

    def close(self):
        """
        Closes the underlying HTTP connection
        """

        self.helper.close()

    def headers(self) -> Optional[hm.HeaderTypes]:
        """
        Inherit this to generate headers that will be sent at each request.
        """

    def cookies(self) -> Optional[hm.CookieTypes]:
        """
        Inherit this to generate cookies to be sent at each request
        """

    def auth(self) -> Optional[hm.AuthTypes]:
        """
        Inherit this to generate auth to be sent at each request
        """

    def follow_redirects(self) -> bool:
        """
        Return False to disable redirects. Also, if a value is specified in the
        decorator then this value will be overridden.
        """

        return True

    def raise_errors(self, resp: httpx.Response, hint: Any) -> None:
        """
        By default, raise errors if HTTP statuses are error status but you
        could do any kind of inspection you want here.

        The hint is there in case you need different mechanisms for different
        paths, the hint is provided through the decorator.
        """

        resp.raise_for_status()

    def decode(self, resp: httpx.Response, hint: Any) -> Any:
        """
        Transforms the HTTP response into viable data. By default it decodes
        JSON but who knows what you might want to support.

        The hint is there in case you need different mechanisms for different
        paths, the hint is provided through the decorator.
        """

        return resp.json()

    def extract(self, data: Any, hint: Any) -> Any:
        """
        Use this method to extract the data before fitting it into a type. By
        example, sometimes APIs will return something like {result: xxx}
        instead of returning your object directly.

        The hint is there in case you need different mechanisms for different
        paths, the hint is provided through the decorator.
        """

        return data

    def on_response(self, request: hm.Request, response: hm.Response) -> None:
        """
        This method is called when the response is received, before any typefit
        logic is applied. Results are ignored.
        Use this method to inspect the request or the response (eg: log some
        request info for debug purposes).

        Modification of either of the objects is strongly discouraged.
        """
