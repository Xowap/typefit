from typefit_hn.api import HackerNews
from typefit_hn.models import Story


def test_get_item():
    hn = HackerNews()
    story = hn.get_item(8863)
    assert isinstance(story, Story)
    assert story.title == "My YC app: Dropbox - Throw away your USB drive"
