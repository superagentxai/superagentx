from agentx.handler.ecommerce.fake_product import FakeProductHandler


class FakeFlipkartHandler(FakeProductHandler):
    _provider: str = 'Flipkart'

    async def product_search(
            self,
            *,
            query: str
    ):
        """
        Performs a search on Flipkart for products matching the given query.

        This method takes a search term (like "laptop" or "smartphone") and looks for relevant
        products on Flipkart. It returns a list of products that match the search, along with
        useful information like their prices, ratings, and descriptions.

        Args:
            query (str): The search term you're using to find products on Flipkart.

        Returns:
            A list of products that match the search query. Each product will include details
            such as its name, price, and other relevant information from Flipkart.

        """
        return await super().search(
            provider=self._provider,
            category=query
        )

    def __dir__(self):
        return (
            "product_search",
        )
