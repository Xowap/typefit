# TypeFit

That's a [Retrofit-inspired](https://square.github.io/retrofit/) library for
Python that will allow you to fit JSON values into native type-annotated Python
objects, making it easier for your IDE/editor to offer you auto-completion on
JSON data and thus helping you to work with APIs and such.

## Quick start

The core idea is very simple. You describe your data structure using type
annotations and the library will fit the JSON data into it.

JSON can produce numbers, bools, strings and nulls. Those are mapped directly
into `int`/`float` (depending on what you set), `bool`, `str` and `None`. There
is also lists which are mapped into `list`.

The "biggest" thing here is mapping dictionaries into `NamedTuple`.

```python
from typefit import typefit
from typing import NamedTuple, Text, List

class Comment(NamedTuple):
    content: Text
    positive: bool

class Article(NamedTuple):
    title: Text
    content: Text
    likes: int
    comments: List[Comment]

data = {
    "title": "My article",
    "content": "This article is awesome",
    "likes": 42,
    "comments": [
        {
            "content": "Awesome",
            "positive": True
        },
        {
            "content": "Crap",
            "positive": False
        },
    ],
}

article = typefit(Article, data)

print(article.title)
# "My article"
```

As you can see, it's quite easy to map API objects into NamedTuple and to
hydrate the data from JSON-ish structures. There is some subtleties but we'll
see that afterward.

## Narrow types

Narrow types are types that allow a more precise parsing of JSON data based on
custom code. Let's dive into an example to make it clear.

```python
from typefit import typefit, narrows
from typing import NamedTuple, Text, List

class Message(NamedTuple):
    content: Text
    date: narrows.DateTime

data = {
    "content": "Hi!",
    "date": "2019-10-19T16:10:03+02:00",
}

message = typefit(Message, data)

print(message.date.to_formatted_date_string())
# "Oct 19, 2019"
```

### Bultins

By default, typefit ships with the following narrow types. If they require a
lib, the lib is listed as an extra dependency and won't be installed by default
so for the feature to work you'll have to install that lib.

- Date/time &mdash; Based on [`pendulum`](https://pendulum.eustace.io/)
    - `DateTime` &mdash; Parses an ISO date/time
    - `Date` &mdash; Parses an ISO date
    - `TimeStamp` &mdash; Parses a Unix timestamp (in seconds)

### Custom

You can provide a custom narrow type simply by creating a type whose
constructor will have exactly a single argument which is properly annotated
(with a simple type like `int` or `Text` but not a generic like `Union` or 
`List`).

A simple example would be:

```python
from typing import Text
from typefit import typefit

class Name:
    def __init__(self, full_name: Text):
        split = full_name.split(' ')
        
        if len(split) != 2:
            raise ValueError('Too many names')

        self.first_name, self.last_name = split

name = typefit(Name, "Rémy Sanchez")
print(name.first_name)
print(name.last_name)
```

However sometimes you just want to wrap a type that already exists but doesn't
have the right arguments in its constructor. That's the case of the 
date-related narrows described above. Let's dissect one.

```python
import pendulum

class TimeStamp(pendulum.DateTime):
    def __new__(cls, date: int):
        return pendulum.from_timestamp(date)
```

You'll probably ask me why is there some funny business with `__new__` instead
of just created a function that will parse and return the desired value. The
answer is that you're doing type annotations so you must provide valid types
otherwise you'll confuse your static type checker, which loses the interest of
annotating types in a first place.
