"""Opt-in Parallel Search through SuperAgentX's existing stdio MCP engine."""

import argparse
import asyncio
import os
from importlib.metadata import version

from superagentx.engine import Engine
from superagentx.handler.mcp import MCPHandler
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


def create_handler() -> MCPHandler:
    """Bridge stdio to the free, keyless Streamable HTTP search endpoint."""
    return MCPHandler(
        command="npx",
        mcp_args=[
            "-y",
            "mcp-remote@0.1.38",
            "https://search.parallel.ai/mcp",
            "--transport",
            "http-only",
            "--enable-proxy",
            "--header",
            f"User-Agent: superagentx/{version('superagentx')}",
        ],
        env=dict(os.environ),
    )


async def search(query: str, llm: LLMClient) -> list[str]:
    """Let the engine select MCP tools and return their text, including sources."""
    handler = create_handler()
    engine = Engine(
        handler=handler,
        llm=llm,
        prompt_template=PromptTemplate(
            system_message="Search the web for the user's question using the available tools. "
            "Include relevant source URLs."
        ),
    )
    try:
        results = await engine.start(input_prompt=query)
        text = []
        for result in results:
            if isinstance(result, str):
                text.append(result)
            else:
                if result.isError:
                    raise RuntimeError(f"Parallel Search returned an error: {result.content}")
                text.extend(block.text for block in result.content if block.type == "text")
        return text
    finally:
        await handler.cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Question to search for")
    parser.add_argument("--model", required=True, help="Your configured tool-capable LLM model")
    parser.add_argument("--llm-type", default="openai", help="SuperAgentX LLM provider type")
    args = parser.parse_args()
    llm = LLMClient(llm_config={"model": args.model, "llm_type": args.llm_type})
    for text in asyncio.run(search(args.query, llm)):
        print(text)


if __name__ == "__main__":
    main()
