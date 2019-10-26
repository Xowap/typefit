# Hacker News API Client

This example app is a demo of an API client that can be used to parse and
understand items coming from the Hacker News API.

All [models](./models.py) are created according to the
[official documentation](https://github.com/HackerNews/API) and describe the
data in order to fit it into Python types.

The [API client](./api.py) itself is a very simple API client that only
supports getting items. The way it is defined will fit the data into the right
class from models.

## Usage

Then you can pretty simply use this library.

```python
from typefit_hn import HackerNews

hn = HackerNews()
story = hn.get_item(42)

print(f"{story.title} ({story.score}): {story.url}")
```

## Models

The models are based on the Python `dataclasses` module because they work quite
well with inheritance and there is a lot of shared fields and logic between
all types, since they all are defined as "items" in the original API.

There is a `BaseItem` class which will, in its `__post_init__()`, check if the
type of the item corresponds to the statically defined `TYPE` that each
sub-class holds. If not, a `ValueError` is raised which allows Typefit to
reject fitting data into this class and to try another one, even if all the
fields were matched.

Another subtle thing comes in the difference between `Story` and `Ask`. Both
those types have the same `type` according to the API, however one will have
an `url` and the other will have a `text`. For this reason, in the
`__post_init__()` of the `Story` there is a check to make sure that a `Story`
cannot have an URL by raising a `ValueError` if so. This will make sure that
the difference between `Story` and `Ask` is well taken in account.
