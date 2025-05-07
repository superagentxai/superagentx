<div align="center">

<img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/fulllogo_transparent.png?raw=True" width="350">


<br/>


**SuperAgentX**: A lightweight autonomous true multi-agent framework with AGI capabilities.

<br/>

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-31210/)
[![GitHub Repo stars](https://img.shields.io/github/stars/superagentxai/superagentX)](https://github.com/superagentxai/superagentX)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/superagentxai/superagentX/blob/master/LICENSE)

</div>

<h1 align="center">SuperAgentX - Multi-Agent, Browser Intelligence and MCP - Made Easy</h1>
<br/><br/>

# Quick start

```bash
pip install superagentx
```

## Browser AI Agent

```python
import asyncio

from superagentx.agent import Agent
from superagentx.browser_engine import BrowserEngine
from superagentx.llm import LLMClient
from superagentx.prompt import PromptTemplate


async def main():
    llm_client: LLMClient = LLMClient(llm_config={'model': 'gpt-4.1', 'llm_type': 'openai'})

    prompt_template = PromptTemplate()

    browser_engine = BrowserEngine(
        llm=llm_client,
        prompt_template=prompt_template,

    )
    query_instruction = ("Which teams have won more than 3 FIFA World Cups, and which team is most likely to win the "
                         "next one?")

    fifo_analyser_agent = Agent(
        goal="Complete user's task.",
        role="You are a Football / Soccer Expert Reviewer",
        llm=llm_client,
        prompt_template=prompt_template,
        max_retry=1,
        engines=[browser_engine]
    )

    result = await fifo_analyser_agent.execute(
        query_instruction=query_instruction
    )

    print(result)


asyncio.run(main())

```
## Run

![image description](https://github.com/superagentxai/superagentx/blob/master/assets/superagentx_browser.gif)

```bash
$ export OPENAI_API_KEY=sk-******************
```

## Key Features

🚀 **Open-Source Framework**: A lightweight, open-source AI framework built for multi-agent applications with Artificial General Intelligence (AGI) capabilities.

🎯 **Goal-Oriented Multi-Agents**: This technology enables the creation of agents with retry mechanisms to achieve set goals. Communication between agents is Parallel, Sequential, or hybrid.

🏖️ **Easy Deployment**: Offers WebSocket, RESTful API, and IO console interfaces for rapid setup of agent-based AI solutions.

♨️ **Streamlined Architecture**: Enterprise-ready scalable and pluggable architecture. No major dependencies; built independently!

📚 **Contextual Memory**: Uses SQL + Vector databases to store and retrieve user-specific context effectively.

🧠 **Flexible LLM Configuration**: Supports simple configuration options of various Gen AI models.

🤝 **Extendable Handlers**: Allows integration with diverse APIs, databases, data warehouses, data lakes, IoT streams, and more, making them accessible for function-calling features.

🤝 **Agentic RPA (Robotic Process Automation)** – SuperAgentX enables computer-use automation for both browser-based and desktop applications, making it an ideal solution for enterprises looking to streamline operations, reduce manual effort, and boost productivity.


## Table of contents
- [What is SuperAgentX?](#what-is-superagentx)
- [Why SuperAgentX?](#why-superagentx)
- [Getting Started](#getting-started)
- [Installing Dependencies](#installing-dependencies)
- [Contribution](#contribution)
- [License](#license)

## What is SuperAgentX?

**The Ultimate Modular Autonomous Agentic AI Framework for Progressing Towards AGI.** <br/><br/>
SuperAgentX is an advanced agentic AI framework designed to accelerate the development of Artificial General Intelligence (AGI). It provides a powerful, modular, and flexible platform for building autonomous AI agents capable of executing complex tasks with minimal human intervention. By integrating cutting-edge AI technologies and promoting efficient, scalable agent behavior, SuperAgentX embodies a critical step forward in the path toward superintelligence and AGI. Whether for research, development, or deployment, SuperAgentX is built to push the boundaries of what's possible with autonomous AI systems.

## Why SuperAgentX?

SuperAgentX addresses the growing need for highly capable, autonomous AI systems that can perform complex tasks with minimal human intervention. As we approach the limits of narrow AI, there's a need for an adaptable and scalable framework to bridge the gap toward AGI (Artificial General Intelligence). Here’s why SuperAgentX stands out:

**Super**: Cutting-edge AI systems with exceptional capabilities, paving the way to **AGI** (Artificial General Intelligence) and **ASI** (Artificial Super Intelligence).</p>
**Agent**: Autonomous Multi AI agent framework designed to make decisions, act independently, and handle complex tasks. </p>
**X**: The unknown, the limitless, the extra factor that makes SuperAgentX revolutionary, futuristic, and transformative.</p>

### Getting Started

```shell
pip install superagentx
```
##### Usage - Example SuperAgentX Code
This SuperAgentX example utilizes two handlers, Amazon and Walmart, to search for product items based on user input from the IO Console.

1. It uses Parallel execution of handler in the agent 
2. Memory Context Enabled
3. LLM configured to OpenAI
4. Pre-requisites

## Architecture
<img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/architecture.png?raw=True" title="SuperAgentX Architecture"/>

## Large Language Models

| Icon                                                                                                                                                          | LLM Name          &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; | Status                                                                                                                                           |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/openai.png?raw=True" title="OpenAI" height="20" width="20"/>              | **OpenAI**                                                                                     | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/azure-icon.png?raw=True" title="Azure OpenAI" height="20" width="20"/>    | **Azure OpenAI**                                                                               | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |  
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/awsbedrock.png?raw=True" title="AWS Bedrock" height="20" width="20"/>     | **AWS Bedrock**                                                                                | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/gemini.png?raw=True" title="Google Gemini" height="20" width="20"/>       | **Google Gemini**                                                                              | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/meta.png?raw=True" title="Google Gemini" height="20" width="20"/>         | **Meta Llama**                                                                                 | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/ollama.png?raw=True" title="Ollama" height="20" width="20"/>              | **Ollama**                                                                                     | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/claude-ai-logo.png?raw=True" title="Claude AI" height="20" width="20"/>   | **Claude AI**                                                                                  | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>   |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/mistral-ai-logo.png?raw=True" title="Mistral AI" height="20" width="30"/> | **Mistral AI**                                                                                 | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/todo.png?raw=True" title="TODO" height="20" width="20"/>          |
| <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/llms/ibm.png?raw=True" title="IBM WatsonX AI" height="20" width="30"/>         | **IBM WatsonX**                                                                                | <img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/todo.png?raw=True" title="TODO" height="20" width="20"/>          |

## Environment Setup
```shell
$ python3.12 -m pip install poetry
$ cd <path-to>/superagentx
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ poetry install
```

## [Documentation](https://docs.superagentx.ai/introduction)

## License

SuperAgentX is released under the [MIT](https://github.com/superagentxai/superagentX/blob/master/LICENSE) License.
