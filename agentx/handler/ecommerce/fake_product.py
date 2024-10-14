import random
import logging
import uuid
from abc import ABC

from openai.types.chat import ChatCompletion

from agentx.handler.base import BaseHandler
from agentx.llm import ChatCompletionParams, LLMClient
from agentx.utils.helper import iter_to_aiter, sync_to_async
from tests.llm.test_bedrock_client import aws_bedrock_client_init

logger = logging.getLogger(__name__)


class FakeProductHandler(BaseHandler, ABC):

    def __init__(
            self,
            *,
            llm_client: LLMClient,
            product_models: list[dict],
            total: int = 5
    ):
        self.llm_client: LLMClient = llm_client
        self.product_models = product_models
        self.total = total

    @staticmethod
    async def _random_rating():
        return {
            "rate": round(random.uniform(2.0, 5.0), 1),
            "count": random.randint(100, 500)
        }

    async def _random_product_description(
            self,
            model,
    ):
        messages = [
            {
                "role": "system",
                "content": f"You are a best product reviewer. Analyze and generate fake product short "
                           f"description for {model.get('name')} with category {model.get('category')} and its features"
            }
        ]

        chat_completion_params = ChatCompletionParams(
            messages=messages,
        )
        response: ChatCompletion = await self.llm_client.achat_completion(
            chat_completion_params=chat_completion_params
        )
        if response and response.choices:
            description = response.choices[0].message.content
            logger.debug(f"Open AI Async ChatCompletion Response {description}")
            return description

    async def _category_found(
            self,
            *,
            name: str,
            category: str,
            query: str
    ) -> bool:
        _categories = [
            _name.strip().lower() for _name in name.split(" ")
        ] + [
            _category.strip().lower() for _category in category.split(",")
        ]
        _categories = " ".join(_categories)
        async for _query in iter_to_aiter(query.split(' ')):
            if _query.lower() in _categories:
                return True
        return False

    async def _generate_data_products(
            self,
            provider: str,
            category: str
    ):
        # Generate the dataset
        products_list = []
        if self.product_models:
            _total = 0
            _exists_names = []
            await sync_to_async(random.shuffle, self.product_models)
            async for model in iter_to_aiter(self.product_models):
                _name = model.get('name')
                _category = model.get('category')
                if _name not in _exists_names:
                    _category_found = await self._category_found(
                        name=_name,
                        category=_category,
                        query=category
                    )
                    if _category_found:
                        product_data = {
                            "id": uuid.uuid4().hex,
                            "title": _name,
                            "price": round(random.uniform(8000, 90000), 2),
                            "description": await self._random_product_description(model),
                            "category": model.get('category'),
                            "provider": provider,
                            "image": f"https://fake{provider.lower()}storeapi.com/img/{_name}.jpg",
                            "rating": await self._random_rating()
                        }
                        products_list.append(product_data)
                        _exists_names.append(_name)
                        _total = _total + 1
                        if _total >= self.total:
                            break
                        # TODO: Random 5 comments generate using LLM!
        return products_list

    async def search(
            self,
            *,
            provider: str,
            category: str
    ):
        """
        Search for a product using the specified provider.

        This function interfaces with multiple e-commerce providers (e.g., Amazon, Flipkart)
        to search for products based on the specified provider.
        parameter:
            provider (str): The name of the e-commerce provider to search from. Supported providers include:
                - 'amazon': Search for products on Amazon.
                - 'flipkart': Search for products on Flipkart.
        Returns:
        The search results as a response object or parsed data, depending on the implementation for each provider.
        """
        return await self._generate_data_products(
            provider=provider,
            category=category
        )
