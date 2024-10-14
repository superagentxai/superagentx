from agentx.handler.ecommerce.fake_product import FakeProductHandler


class FakeAmazonHandler(FakeProductHandler):
    _provider: str = 'Amazon'

    async def product_search(
            self,
            *,
            query: str
    ):
        """
        Searches for products on Amazon based on the given keyword.

        This method helps you find products on Amazon by using a search term like "laptop" or
        "headphones." It will return a list of items that match what you're looking for, along
        with important details like the product name, price, ratings, comments, and other feedback from customers.

        Args:
            query (str): The word or phrase you want to search for on Amazon.

        Returns:
            A list of products that match your search term, with information about each item.
        """
        return await super().search(
            provider=self._provider,
            category=query
        )

    def __dir__(self):
        return (
            "product_search",
        )
