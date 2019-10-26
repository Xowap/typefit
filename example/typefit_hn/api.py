from typefit import api
from .models import Item


class HackerNews(api.SyncClient):
    """
    Example Hacker News API client
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0/"

    @api.get("item/{item_id}.json")
    def get_item(self, item_id: int) -> Item:
        """
        Retrieves an item. Actual returned type depends on the type of the
        item. See the model classes to get an idea of the different types.
        """
