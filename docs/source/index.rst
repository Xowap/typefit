Welcome to Typefit's documentation!
===================================

Typefit is a Retrofit-inspired library for Python that helps you fitting
decoded JSON data into Python type-annotated structures.

.. code-block:: python

    from typefit import api
    from typing import NamedTuple, Text


    class Item(NamedTuple):
        id: int
        title: Text


    class HackerNews(api.SyncClient):
        BASE_URL = "https://hacker-news.firebaseio.com/v0/"

        @api.get("item/{item_id}.json")
        def get_item(self, item_id: int) -> Item:
            pass

    story = HackerNews().get(42)
    print(story.title)
    # An alternative to VC: &#34;Selling In&#34;

Why?
----

Using this approach, you describe API objects to your typing annotations
processor and thus make your API client type-safe. The auto-completion of your
editor starts working and you know exactly what should expect from your data.

What?
-----

Typefit provides several modules to help you.

.. toctree::
   :maxdepth: 2

   typefit
   Building API clients <api>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
