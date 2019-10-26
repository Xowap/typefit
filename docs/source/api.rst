Building API clients
====================

The reason Typefit was built is to consume APIs. But instead of just letting
you handle all the boring boilerplate and telling you to parse the output of
your functions with :py:func:`typefit.typefit`, it will handle the boilerplate
for you and just let you describe what your API looks like.

This guide is intended to cover the main aspects of the Typefit API generator
but it is advised to read it in the writing order since concepts are introduced
progressively over the page.

.. note::

    I can hear your thoughts out loud right now, thinking that this is neat but
    for real production APIs it's probably just an impractical dream. Well,
    maybe but one of the design goals is to have many orthogonal concepts that
    you can easily customize individually. Please open an issue if you find an
    API that you can't work with using Typefit!

In this page we'll use `httpbin <https://httpbin.org/>`_ to demonstrate how
you can make use of the API client generator.

.. note::

    This whole thing depends on ``httpx`` however Typefit doesn't depend on it
    by default so you need to add ``httpx`` to the requirements of your
    project.

Defining models
---------------

The first step in building an API client is to define your models. To begin
with we'll do a GET query, so let's build the GET model.

.. code-block:: python

    HttpArg = Union[Text, List[Text]]
    HttpArgs = Dict[Text, HttpArg]
    HttpHeaders = Dict[Text, Text]


    class HttpGet(NamedTuple):
        args: HttpArgs
        headers: HttpHeaders
        origin: Text
        url: Text

This lets us define what the output from the server should look like. That's
the type into which the response will be fitted.

Making a GET request
--------------------

Then let's build our API:

.. code-block:: python

    from typefit import api

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        @api.get("get?value={value}")
        def get(self, value: Text) -> HttpGet:
            pass

The API client generator will look at the signature of your methods and
generate the code that is required for this method to work. You need not write
any code inside the method, it will never be called.

As you can see, the specified URL is formatted using the standard
`format <https://pyformat.info/>`_ syntax and the method's arguments, except
that all arguments will be safely URL-encoded.

.. code-block:: python

    get = Bin().get("foo bar")
    assert get.args["value"] == "foo bar"

Let's walk through what happens:

1. :code:`get("foo bar")` is called
2. The path template ``get?value={value}`` becomes the path ``get?value=foo+bar``
3. The path is joined to the ``BASE_URL`` to become
   `https://httpbin.org/get?value=foo+bar <https://httpbin.org/get?value=foo+bar>`_
4. The request is made
5. The output JSON is fitted inside ``HttpGet`` and returned

.. note::

    It is expected that the API will return JSON data. If not, please see below
    how to change API output decoding.

Alternate specification of GET query
++++++++++++++++++++++++++++++++++++

To specify the GET parameters that you're going to send you might prefer using
the ``params`` parameter which takes a dictionary as argument and allows you
to define the GET query to be sent. The above example would be equivalent to:

.. code-block:: python

    from typefit import api

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        @api.get("get", params: lambda value: {"value": value})
        def get(self, value: Text) -> HttpGet:
            pass

That is more verbose but in some cases much more convenient to build.

Complex URL generation
----------------------

In case you need a more complex URL generation method, you can provide a
callable as path instead of just giving a static string. By example:

.. code-block:: python

    from typefit import api

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.count = 0

        def get_url(self, value: int) -> Text:
            """
            This method counts the number of requests done and adds a parameter
            which indicates if this request is odd or even.
            """

            self.count += 1

            if self.count % 2:
                parity = "odd"
            else:
                parity = "even"

            return f"get?parity={parity}&value={value}"

        @api.get(get_url)
        def get(self, value: int) -> HttpGet:
            pass

Here you can see that a callable is passed to generate the path. The callable
is called for each request. It receives its arguments based on their name:
if they have the same name as the arguments found in the method's signature
then it will get called. This callable can be an unbound method (like here),
an inline lambda or an external function. Any callable will do as long as the
arguments have the right name!

.. code-block:: python

    b = Bin()

    print(b.get(42).args)
    # {'parity': 'even', 'value': '42'}

    print(b.get(42).args)
    # {'parity': 'odd', 'value': '42'}

Custom headers
--------------

Almost every API will require that you provide some form of authentication
in the headers. Typefit provides you several ways to specify custom headers.

.. code-block:: python

    from httpx import models as hm

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        def headers(self) -> Optional[hm.HeaderTypes]:
            return {"Authorization": "Bearer xxxxxxxx"}

        @api.get("get")
        def get(self) -> HttpGet:
            pass

    get = Bin().get()
    assert get.headers["Authorization"] == "Bearer xxxxxxxx"

You can see that there is a ``headers()`` method that you can implement in
order to provide headers which will be added to each request. The method is
evaluated before each call so you can change the return value over time.

.. note::

    You'll notice that the ``headers()`` method's return type is
    ``hm.HeaderTypes``. Here, ``hm`` is an alias of the ``httpx.models``
    module, since the whole API client generator is based on
    `httpx <https://github.com/encode/httpx>`_. The reasons behind that choice
    over the extra-popular ``requests`` are multiple:

    - ``httpx`` enforces timeouts while ``requests`` doesn't, which is
      dangerous since lingering requests can hang a thread or a process
      forever and cause serious reliability issues
    - ``httpx`` is fully type annotated, which is really fitting with the mood
      of this module
    - And finally, ``httpx`` supports a synchronous and asynchronous API and
      provides a pluggable system to manage connection pooling (either via
      the async loop, either via threading, etc)

    Overall, **the API exposed by Typefit is very transparent above httpx**.
    This is really just some boilerplate over ``httpx``.

But if instead of defining global headers you want to control the headers for
one specific request, you can also specify your headers in the decorator.

.. code-block:: python

        @api.get("get", headers={"Authorization": "Bearer xxxxxxxx"})
        def get(self) -> HttpGet:
            pass

And finally, you'll quickly realize that all parameters of that decorator can
either be static values, either be callables. The same rules apply as explained
above.

.. code-block:: python

        @api.get("get", headers=lambda bearer: {
            "Authorization": f"Bearer {bearer}",
        })
        def get(self, bearer: Text) -> HttpGet:
            pass

Such a code lets you define headers that depend on the method's parameters
directly. Passed parameters are matched based on their name, so here the
``bearer`` parameter from the method will get passed to the ``headers`` lambda
when evaluated.

.. note::

    When you specify headers through *both* the ``headers()`` method and the
    decorator parameter, then both values will be merged with a priority given
    to the decorator's parameter.

Sending POST/PUT/PATCH data
---------------------------

Of course, no API generator could be complete if it didn't allow you to send
actual POST data to the API. As Typefit uses ``httpx``, all three arguments
are exposed through the constructor:

- ``data`` is regular form data, it's basically a dictionary with all the data
  that will get form-encoded
- ``json`` will serialize the provided object into JSON and send it to the API
  with the appropriate ``Content-Type`` header
- ``files`` contains a dictionary of files to be sent in a multipart-encoded
  form

.. note::

    As for every other parameter, you can either pass a static value either
    pass a callable which will be invoked for each request. Once the value
    resolved, it is passed as-is to ``httpx``. To get more detailed information
    you should have a look at
    `the official httpx documentation <https://www.encode.io/httpx/quickstart/#sending-form-encoded-data>`_
    as well as the
    `httpx types definitions <https://github.com/encode/httpx/blob/master/httpx/models.py>`_.

Let's consider that we want to send JSON data to the remote API, because that's
usually what we want to do.

The simplest thing we can do is just to send static data, by example:

.. code-block:: python

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        @api.post("post", json={"foo": "bar"})
        def my_post_method(self) -> HttpPost:
            pass

    bin = Bin()
    post = bin.my_post_method()
    assert post.json == {"foo": "bar"}

Of course, this can be replaced by a dynamic value based on the method's
parameters.

.. code-block:: python

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        @api.post("post", json=lambda foo: {"foo": foo})
        def my_post_method(self, foo: Text) -> HttpPost:
            pass

    bin = Bin()
    post = bin.my_post_method("bar")
    assert post.json == {"foo": "bar"}

Using this callable technique, you can send arbitrary data to the API based
on your parameters, even if the parameters are complex Python types. It is
worth noting that just like above the ``json`` callable could be any callable,
including an actual method of the object.

And finally, this example uses the ``@api.post`` decorator but the ``@api.put``
and ``@api.patch`` are also available with the same syntax.

Other arguments and parameters
------------------------------

Eventually the goal is to support fully ``httpx``, however the goal of this
specific release is to support the bare minimum in order for the library to be
viable. The core use cases are detailed above, however more parameters are
translated today.

Overall logic
+++++++++++++

The building of a request lies on 3 different layers:

1. The API client builder is based on httpx's
   `Client <https://www.encode.io/httpx/advanced/#client-instances>`_ so
   cookies will be persisted from one request to the other
2. Overridable methods of the :py:class:`typefit.api.SyncClient` allow you set
   values indistinctly on all requests
3. The decorator of your HTTP methods also allows you to set those values
   individually for each method

The idea is that parameters are evaluated in order and then merged or
overridden (depending on which makes sense) with the next layer. So by example
if you have a cookie persisted in the Client and you define another cookie
in the method's decorator then both cookies will be sent. On the other hand
if a cookie is persisted in the Client but the decorator sets the same cookie
then the decorator's value will be sent instead of the persisted one.

Decorator arguments evaluation
++++++++++++++++++++++++++++++

To give you a total flexibility in what you can send from the decorator, all
arguments can either be a static value or a callable. You can observe both
cases in the examples above.

If callable, the callable will be called for each request and arguments found
to have the same name as an argument in the generated method will be
automatically passed to the callable

Values are passed as-is to ``httpx`` and thus you can refer to the ``httpx``
documentation for a full reference.

Available arguments
+++++++++++++++++++

In addition to the request path and the POST/GET/PUT data parameters that have
been explained above, those ``httpx`` arguments are available.

``headers()``
~~~~~~~~~~~~~

This has been mentioned before but is worth repeating here.

.. code-block:: python

    from httpx import models as hm

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        def headers(self) -> Optional[hm.HeaderTypes]:
            return {"Foo": "Bar"}

        @api.get("get", headers={"Answer": "42"})
        def get(self) -> HttpGet:
            pass

    get = Bin().get()
    assert get.headers = {
        "Foo": "Bar",
        "Answer": "42",
    }

Headers can be returned by the :py:meth:`typefit.api.SyncClient.headers` method
or come from the decorator's arguments.

To demonstrate the resolution of callable arguments, you can also do

.. code-block:: python

        @api.get("get", headers=lambda answer: {"Answer": str(answer)})
        def get(self, answer: int) -> HttpGet:
            pass

``cookies()``
~~~~~~~~~~~~~

Cookies work exactly the same way as headers do. The only difference is that
cookies set by the server will persist afterwards.

Here is how that would work:

.. code-block:: python

    class HttpCookies(NamedTuple):
        cookies: Dict[Text, Text]

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        def cookies(self) -> Optional[hm.CookieTypes]:
            return {"global_cookie": "hello"}

        @api.get("cookies/set/{name}/{value}")
        def set_cookie(self, name: Text, value: Text) -> HttpCookies:
            pass

        @api.get("cookies", cookies={"local_cookie": "hi"})
        def get_cookies(self) -> HttpCookies:
            pass

    bin = Bin()

    bin.set_cookie("set_cookie", "howdy")

    assert bin.get_cookies().cookies == {
        "set_cookie": "howdy",
        "global_cookie": "hello",
        "local_cookie": "hi",
    }

This example demonstrates how you can set a cookie in the session (through
httpbin's cookie setting feature), have one coming from the global method and
one defined locally on the ``get_cookies()`` method.

All three cookies get merged and httpbin's ``cookies`` call returns the three
of them.

``auth()``
~~~~~~~~~~

On the contrary to cookies and headers, you can only send one auth for each
request. If you want to specify the auth parameter you can return a
non-``None`` value. The value specified in the decorator will of course take
precedence over the value defined in the ``auth()`` method.

.. code-block:: python

    class HttpAuth(NamedTuple):
        authenticated: bool
        user: Text

    class Bin(api.SyncClient):
        BASE_URL = "https://httpbin.org/"

        def auth(self) -> Optional[hm.AuthTypes]:
            return "test_user", "test_password"

        @api.get("basic-auth/test_user/test_password")
        def success_auth(self) -> HttpAuth:
            pass

        @api.get("basic-auth/test_user/test_password", auth=("wrong", "wrong"))
        def fail_auth(self) -> HttpAuth:
            pass

    bin = Bin()

    assert bin.success_auth().authenticated
    assert not bin.success_auth().authenticated  # this will raise an exception

There we use the ``basic-auth/test_user/test_password`` call of httpbin which
will trigger an HTTP basic auth using ``test_user`` as username and
``test_password`` as password.

We defined a ``success_auth()`` method which has no ``auth`` parameter in its
arguments, meaning that the value of the ``auth`` parameter given to ``httpx``
is determined by the output of the ``auth()`` method.

There is also a ``fail_auth()`` method, which overrides the ``auth`` argument
with a ``("wrong", "wrong")`` tuple. This will cause the authentication to fail
and an exception to be risen because those are not the username/passwords that
the API will expect.

``allow_redirect()``
~~~~~~~~~~~~~~~~~~~~

Indicates to ``httpx`` if it should follow redirects or not. Like ``auth``, it
is not something you can merge so if the decorator returns a value it will
override the output of the method.

.. code-block:: python

    class Bin(api.SyncClient):
        BASE_URL = bin_url

        def allow_redirects(self) -> bool:
            return False

        @api.get("redirect/1", allow_redirects=True)
        def redirect(self) -> HttpGet:
            pass

We disable redirects globally using the method but specifically for the
``redirect()`` method we override that and define that we allow redirects.

.. code-block:: python

    redirect = Bin().redirect()
    assert redirect.url.endswith("/get")

As a result, when you execute the query and check the output, you'll notice
that we have been sent to the the ``/get`` endpoint.

Decoding responses
------------------

By default, the client makes a few assumptions:

- The remote API will respect HTTP status codes and thus if the server is
  returning an error it will show in the status code
- The reply will always be a JSON document
- The whole document is to be fitted into a type

However, it is far from always being true. For this reason, it exists methods
that you can override in order to alter the decoding process.

Now, let's suppose that instead of using a regular JSON REST API we're dealing
with some smarty pants who thought that it'd be simpler to output YAML.
Hypothetically, it would return those replies to the example requests.

``GET /article/42``

.. code-block:: yaml

    status: "ok"
    result:
        id: 42
        title: "I love sausages"
        content: "Sausages are good, I love sausages"

``GET /article/nope``

.. code-block:: yaml

    status: "error"
    result:
        message: "Not found"

``decode()``
++++++++++++

Very obviously you can't rely on the default decode method which will expect
some JSON.

.. code-block:: python

    def decode(self, resp: httpx.Response, hint: Any) -> Any:
        return yaml.safe_load(resp.text)

``raise_errors()``
++++++++++++++++++

Now we also want to know if our request was successful

.. code-block:: python

    def raise_errors(self, resp: httpx.Response, hint: Any) -> None:
        super().raise_errors(resp, hint)

        data = self.decode(resp, hint)
        if data.get("status") != "ok":
            raise httpx.HTTPError

We keep the call to the parent which will check the HTTP status code (we
never know maybe there will be an error 5xx) but then we decode the YAML value
and raise an error if we can't find the ``status: "ok"`` in the YAML document.

``extract()``
+++++++++++++

The last part of our pipeline would be the extract function, which takes the
interesting value out and returns it.

.. code-block:: python

    def extract(self, data: Any, hint: Any) -> Any:
        return data["result"]

It's the content of the ``result`` key that interests us for type-fitting, so
that's what we're returning.

Overall
+++++++

Let's now put this together.

.. code-block:: python

    class Article(NamedTuple):
        id: int
        title: Text
        content: Text

    class StupidApiClient(api.SyncClient):
        BASE_URL = "http://stupid.api/v1/"

        def decode(self, resp: httpx.Response, hint: Any) -> Any:
            return yaml.safe_load(resp.text)

        def raise_errors(self, resp: httpx.Response, hint: Any) -> None:
            super().raise_errors(resp, hint)

            data = self.decode(resp, hint)
            if data.get("status") != "ok":
                raise httpx.HTTPError

        def extract(self, data: Any, hint: Any) -> Any:
            return data["result"]

        @api.get("article/{id}")
        def get_article(self, id: int) -> Article:
            pass

And then you can call the Stupid API (well you could if it existed):

.. code-block:: python

    stupid_api = StupidApiClient()
    article = stupid_api.get_article(42)
    assert article.title == "I love sausages"

Hint
++++

You'll notice the ``hint`` argument at we've ignored so far. That's because
some APIs like to make the data extraction complicated by putting the data in
a different key every time. Let's consider an API that lets us retrieve
``broccoli`` and ``carrots``.

``GET /broccoli/42``

.. code-block:: javascript

    {
        "broccoli": {
            "tastes_good": false
        }
    }

``GET /carrots/42``

.. code-block:: javascript

    {
        "carrot": {
            "rabbits_like_it": true
        }
    }

Thanks to the hint, we're going to be able to know how to decode our data.

.. code-block:: python

    class Broccoli(NamedTuple):
        tastes_good: bool

    class Carrot(NamedTuple):
        rabbits_like_it: bool

    class VegetableApi(api.SyncClient):
        BASE_URL = "http://vegetable.api/v1/"

        def extract(self, data: Any, hint: Any) -> Any:
            return data[hint]

        @api.get("broccoli/{id}", hint="broccoli")
        def get_broccoli(self, id: int) -> Broccoli:
            pass

        @api.get("carrot/{id}", hint="carrot")
        def get_carrot(self, id: int) -> Carrot:
            pass

Here the hint is just a string but in fact it could be anything. It is
forwarded to your functions without interpretation in the middle, that value is
totally opaque to Typefit.

.. note::

    Broccoli here is simply used as an example and tries in no way to be
    harmful to the Broccoli Lovers community. Everyone is entitled to like or
    dislike whichever food they want even if this choice tastes incredibly bad
    like broccoli. Also I have a broccoli-loving friend.

Reference
---------

You will find here the detailed reference of all available decorators and
classes in the API client builder module.

.. automodule:: typefit.api
    :members:
