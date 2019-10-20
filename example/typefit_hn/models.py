from typing import Text, List, Union
from typefit import narrows
from dataclasses import dataclass


@dataclass(frozen=True)
class BaseItem:
    TYPE = "story"

    by: Text
    id: int
    type: Text
    time: narrows.TimeStamp

    def __post_init__(self):
        if self.type != self.TYPE:
            raise ValueError


@dataclass(frozen=True)
class BaseStory(BaseItem):
    TYPE = "story"

    descendants: int
    kids: List[int]
    score: int
    title: Text
    url: Text


@dataclass(frozen=True)
class Story(BaseStory):
    def __post_init__(self):
        super().__post_init__()

        if self.__class__ is Story:
            if not self.url:
                raise ValueError


@dataclass(frozen=True)
class Ask(Story):
    text: Text


@dataclass(frozen=True)
class Comment(BaseItem):
    TYPE = "comment"

    kids: List[int]
    parent: int
    text: Text


@dataclass(frozen=True)
class Job(BaseItem):
    TYPE = "job"

    score: int
    text: Text
    title: Text
    url: Text


@dataclass(frozen=True)
class Poll(BaseItem):
    TYPE = "poll"

    descendants: int
    kids: List[int]
    parts: List[int]
    score: int
    text: Text
    title: Text


@dataclass(frozen=True)
class PollOption(BaseItem):
    TYPE = "pollopt"

    poll: int
    score: int
    text: Text


Item = Union[Story, Ask, Comment, Job, Poll, PollOption]
