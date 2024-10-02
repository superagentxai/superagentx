import random
import logging

from openai.types.chat import ChatCompletion

from agentx.llm import LLMClient, ChatCompletionParams

logger = logging.getLogger(__name__)


async def initialize_llm() -> LLMClient:
    llm_config = {'model': 'gpt-4-turbo-2024-04-09', 'llm_type': 'openai'}

    llm_client: LLMClient = LLMClient(llm_config=llm_config)
    return llm_client


# Define random data generators for the dataset
async def random_rating():
    return {
        "rate": round(random.uniform(2.0, 5.0), 1),
        "count": random.randint(100, 500)
    }


async def random_product_description(model: str, llm_client: LLMClient) -> str:
    """
    Generate Product random description with the help of LLM and send it to the item list.
    @param model:
    @param llm_client:
    @return: str
    """
    messages = [
        {
            "role": "system",
            "content": f"You are a best product reviewer. Analyze and generate fake product short description for {model} and its features"
        }
    ]

    chat_completion_params = ChatCompletionParams(
        messages=messages,
    )
    response: ChatCompletion = await llm_client.achat_completion(chat_completion_params=chat_completion_params)
    description = response.choices[0].message.content
    logger.debug(f"Open AI Async ChatCompletion Response {description}")

    return description


async def generate_data_products(product_models: list[str], total: int = 100, provider: str = 'Amazon') -> list[dict]:
    """
    Generate product items list based on the product models.

    @param product_models: product model names
    @param total: number of items to be generated
    @param provider: Amazon / Flipkart / Target etc.
    @return: list of dict in the following format

        product_data = [{
                "id": 12,
                "title": iPhone 15,
                "price": 740$,
                "description": Introducing the iPhone 15, Apple’s latest marvel that seamlessly blends cutting-edge
                                technology with exquisite design, setting a new benchmark for smartphones.
                                The iPhone 15 boasts an advanced dual-camera system that delivers unparalleled photo and
                                video quality, ideal for capturing life’s moments with stunning clarity and color accuracy.,
                "category": "mobile phones",
                "provider": Amazon,
                "image": f"https://fakeamazonstoreapi.com/img/{model}.jpg",
                "rating": 4.7
            }]
    """
    llm_client = await initialize_llm()
    # Generate the dataset
    products_list = []
    if product_models:
        for i in range(1, total):
            model = random.choice(product_models)

            product_data = {
                "id": i,
                "title": model,
                "price": round(random.uniform(8000, 90000), 2),
                "description": await random_product_description(model, llm_client),
                "category": "mobile phones",
                "provider": provider,
                "image": f"https://fake{provider.lower()}storeapi.com/img/{model}.jpg",
                "rating": await random_rating()
            }
            products_list.append(product_data)
            # TODO: Random 5 comments generate using LLM!
    return products_list
