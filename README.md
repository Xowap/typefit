# TypeFit

[![Read the Docs](https://img.shields.io/readthedocs/typefit)](http://typefit.rtfd.io/)
[![Build Status](https://github.com/Xowap/typefit/actions/workflows/run-tests.yaml/badge.svg)](https://github.com/Xowap/typefit/actions/workflows/run-tests.yaml)

Typing annotations make Python awesome, however it's complicated to keep your
data annotated when it comes from external sources like APIs. The goal of
Typefit is to help you map that external data into type-annotated native Python
objects.

```python
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

story = HackerNews().get_item(42)
print(story.title)
# An alternative to VC: &#34;Selling In&#34;
```

This is the full example of a Hacker News API client. Its functionality is
limited but in 14 lines counting white space you can build a type-safe client
for Hacker News. You'll find a [full example](example/typefit_hn) attached if
you're interested.

## Documentation

[✨ **Documentation is there** ✨](http://typefit.rtfd.io/)

## Licence

This library is provided under the terms of the [WTFPL](./LICENSE).

If you find it useful, you can have a look at the
[contributors](https://github.com/Xowap/typefit/graphs/contributors) page to
know who helped.
