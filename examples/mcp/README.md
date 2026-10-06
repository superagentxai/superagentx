# Parallel Search

`parallel_search.py` connects the existing `MCPHandler` and `Engine` to
[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp). Search is free and
requires no Parallel API key. This example is opt-in; run it explicitly or import
`create_handler()` into your own engine. Existing handlers and provider defaults
are unchanged.

Install SuperAgentX using the repository's environment instructions, and install
Node.js 20 or newer with `npx` on your `PATH`. From the repository root:

```sh
python -m examples.mcp.parallel_search --help
# Configure credentials for your chosen LLM provider first.
python -m examples.mcp.parallel_search \
  --llm-type openai --model "$SEARCH_LLM_MODEL" \
  "What does the Python documentation say about asyncio TaskGroup?"
```

Set `SEARCH_LLM_MODEL` to a tool-capable model available to your account and, for
the OpenAI provider above, set `OPENAI_API_KEY`. The LLM selects the search tools;
its provider may charge for that step. The command prints the tools' text results
with source URLs, rather than synthesizing another answer with the LLM.

SuperAgentX currently supports stdio and SSE MCP connections. The example uses
the pinned `mcp-remote@0.1.38` stdio bridge with `--transport http-only` to reach
`https://search.parallel.ai/mcp` via Streamable HTTP. `npx -y` downloads the bridge
on first use, so npm registry access is needed. No OAuth setup or Parallel
credentials are needed. The bridge sends `User-Agent: superagentx/<installed
version>` for discovery and tool requests. Failures propagate to the caller and
the example closes its MCP resources in a `finally` block.

The subprocess inherits the current environment. `--enable-proxy` honors existing
`HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` settings; it does not configure a new
proxy. Custom CA certificates can be supplied with `NODE_EXTRA_CA_CERTS`.

The focused tests use a deterministic tool selector instead of an external LLM.
The live check exercises the same example and engine with real discovery and
search, and requires network access and Node.js:

```sh
python -m pytest -q tests/handlers/test_parallel_search_example.py
PARALLEL_MCP_LIVE=1 python -m pytest -q \
  tests/handlers/test_parallel_search_example.py -k live
```
