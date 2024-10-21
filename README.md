<div align="center">

<img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/fulllogo_transparent.png?raw=True" width="350">


<br/>


**SuperAgentX**: The Ultimate Modular Autonomous Agentic AGI Framework for Progressing Towards AGI.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![GitHub Repo stars](https://img.shields.io/github/stars/decisionfacts/agentX)](https://github.com/decisionfacts/superagentX)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/decisionfacts/superagentX/blob/master/LICENSE)

</div>

## Table of contents
- [What is SuperAgentX?](#what-is-superagentx)
- [Why SuperAgentX?](#why-superagentx)
- [Getting Started](#getting-started)
- [Key Features](#key-features)
- [Installing Dependencies](#installing-dependencies)
- [Contribution](#contribution)
- [License](#license)

## What is SuperAgentX?

**The Ultimate Modular Autonomous Agentic AGI Framework for Progressing Towards AGI.** <br/><br/>
SuperAgentX is an advanced agentic AI framework designed to accelerate the development of Artificial General Intelligence (AGI). It provides a powerful, modular, and flexible platform for building autonomous AI agents capable of executing complex tasks with minimal human intervention. By integrating cutting-edge AI technologies and promoting efficient, scalable agent behavior, SuperAgentX embodies a critical step forward in the path towards superintelligence and AGI. Whether for research, development, or deployment, SuperAgentX is built to push the boundaries of what's possible with autonomous AI systems.

## Why SuperAgentX?

SuperAgentX is designed to address the growing need for highly capable, autonomous AI systems that can perform complex tasks with minimal human intervention. As we approach the limits of narrow AI, there's a need for an adaptable and scalable framework to bridge the gap toward AGI (Artificial General Intelligence). Here’s why SuperAgentX stands out:

**Super** : Cutting-edge AI systems with exceptional capabilities, paving the way to **AGI** (Artificial General Intelligence) and **ASI** (Artificial Super Intelligence).</p>
**Agent** : Autonomous Multi AI agent framework designed to make decisions, act independently, and handle complex tasks. </p>
**X**     : The unknown, the limitless, the extra factor that makes SuperAgentX revolutionary, futuristic, and transformative.</p>

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

Set OpenAI Key:  
```shell
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxx
```

Set Rapid API Key <a href="https://rapidapi.com/auth/sign-up" target="_blank">Free Subscription</a> for Amazon, Walmart Search APIs
```shell
export RAPID_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXX
```

```python 
# Additional lib needs to install
# pip install superagentx-handlers
# python3 superagentx_examples/ecom_iopipe.py

import asyncio
import os
import sys

from rich import print as rprint

from superagentx.memory import Memory

sys.path.extend([os.path.dirname(os.path.dirname(os.path.abspath(__file__)))])

from superagentx.agent import Agent
from superagentx.engine import Engine
from superagentx.llm import LLMClient
from superagentx.agentxpipe import AgentXPipe
from superagentx.pipeimpl.iopipe import IOPipe
from superagentx.prompt import PromptTemplate
from superagentx_handlers.ecommerce.amazon import AmazonHandler
from superagentx_handlers.ecommerce.walmart import WalmartHandler


async def main():
    """
    Launches the e-commerce pipeline console client for processing requests and handling data.
    """

    # LLM Configuration
    llm_config = {'llm_type': 'openai'}
    llm_client: LLMClient = LLMClient(llm_config=llm_config)

    # Enable Memory
    memory = Memory()

    # Add Two Handlers (Tools) - Amazon, Walmart
    amazon_ecom_handler = AmazonHandler()
    walmart_ecom_handler = WalmartHandler()

    # Prompt Template
    prompt_template = PromptTemplate()

    # Amazon & Walmart Engine to execute handlers
    amazon_engine = Engine(
        handler=amazon_ecom_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )
    walmart_engine = Engine(
        handler=walmart_ecom_handler,
        llm=llm_client,
        prompt_template=prompt_template
    )

    # Create Agent with Amazon, Walmart Engines execute in Parallel - Search Products from user prompts
    ecom_agent = Agent(
        name='Ecom Agent',
        goal="Get me the best search results",
        role="You are the best product searcher",
        llm=llm_client,
        prompt_template=prompt_template,
        engines=[[amazon_engine, walmart_engine]]
    )

    # Pipe Interface to send it to public accessible interface (Cli Console / WebSocket / Restful API)
    pipe = AgentXPipe(
        agents=[ecom_agent],
        memory=memory
    )

    # Create IO Cli Console - Interface
    io_pipe = IOPipe(
        search_name='SuperAgentX Ecom',
        agentx_pipe=pipe,
        read_prompt=f"\n[bold green]Enter your search here"
    )
    await io_pipe.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        rprint("\nUser canceled the [bold yellow][i]pipe[/i]!")

```
##### Usage - Example SuperAgentX Result
SuperAgentX searches for product items requested by the user in the console, validates them against the set goal, and returns the result. It retains the context, allowing it to respond to the user's next prompt in the IO Console intelligently. 

![Output](https://github.com/decisionfacts/superagentX/blob/master/docs/images/examples/ecom-output-console.png?raw=True)

## Architecture
<img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/architecture.png?raw=True" title="SuperAgentX Architecture"/>

## Large Language Models

| Icon                                                                                                                                    | LLM Name          &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; | Status                                                                                   |
|-----------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/openai.png?raw=True" title="OpenAI" height="20" width="20"/> | **OpenAI** &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;        | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>           |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/azure-icon.png?raw=True" title="Azure OpenAI" height="20" width="20"/>                                              | **Azure OpenAI**                                                                               | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/checkmark.png?raw=True" title="Tested" height="20" width="20"/>           |  
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/awsbedrock.png?raw=True" title="AWS Bedrock" height="20" width="20"/>                                               | **AWS Bedrock**                                                                                | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/beta.png?raw=True" title="Testing Inprogress" height="20" width="20"/>    |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/gemini.png?raw=True" title="Google Gemini" height="20" width="20"/>                                                 | **Google Gemini**                                                                              | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/wip.png?raw=True" title="Development Inprogress" height="20" width="20"/> |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/meta.png?raw=True" title="Google Gemini" height="20" width="20"/>                                                   | **Meta Llama**                                                                                 | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/wip.png?raw=True" title="Development Inprogress" height="20" width="20"/> |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/ollama.png?raw=True" title="Ollama" height="20" width="20"/>                                                        | **Ollama**                                                                                     | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/wip.png?raw=True" title="Development Inprogress" height="20" width="20"/> |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/claude-ai-logo.png?raw=True" title="Claude AI" height="20" width="20"/>                                             | **Claude AI**                                                                                  | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/todo.png?raw=True" title="TODO" height="20" width="20"/>                  |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/mistral-ai-logo.png?raw=True" title="Mistral AI" height="20" width="30"/>                                           | **Mistral AI**                                                                                 | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/todo.png?raw=True" title="TODO" height="20" width="20"/>                  |
| <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/llms/ibm.png?raw=True" title="IBM WatsonX AI" height="20" width="30"/>                                                   | **IBM WatsonX**                                                                                | <img src="https://github.com/decisionfacts/superagentX/blob/master/docs/images/todo.png?raw=True" title="TODO" height="20" width="20"/>                  |


## Key Features

#### Easy-to-Publish Interfaces
**Pipe** - WebSocket, Interactive Cli Console, and RESTFul API (Coming Soon) enable a smooth and real-time interface for users and systems to interact with SuperAgentX. 

#### Advanced Handler Engines
Handler Engines (Tools) operate either in parallel or sequentially, passing the output from one engine to the input of another. This flexible orchestration enhances efficiency, allowing agents to work in perfect harmony for complex tasks.

#### Multi-Mode Agents
Goal oriented agents with auto retry feature based on threshold, helps to achieve expected results. SuperAgentX supports agents running in parallel, sequential, or a hybrid mode (a combination of both). This ensures optimized task execution, whether processes are dependent or independent.

#### Intelligent Context Memory
A robust Context Memory captures user interactions and environmental data, enabling the system to provide efficient RAG (Retrieval-Augmented Generation) search features, significantly reducing operational costs by handling data intelligently.

#### Ease of Configuration for LLM Support in SuperAgentX
SuperAgentX supports multiple LLMs, including **OpenAI**, **Azure OpenAI**, **AWS Bedrock LLMs**, **Llama 3+**, **Gemini AI**, **Claude AI**, **Ollama** and **IBM WatsonX** is designed to effortlessly integrate with a variety of Large Language Models (LLMs), providing a smooth and flexible setup process.

#### Continuous Learning
Through built-in feedback mechanisms, SuperAgentX continuously learns and adapts, allowing it to memorize and improve its performance for future interactions.

#### Adaptability and Personalization
Highly adaptable and flexible, SuperAgentX can be extended and trained to create personalized **AGI** (Artificial General Intelligence) systems, ensuring that it meets specific needs and scenarios.

#### Simplified Autonomous Framework
The **Autonomous Multi-Agent Framework** simplifies the deployment of intelligent, autonomous systems, offering a foundation with **AGI** extendability capabilities, enabling a smooth evolution toward general intelligence.


## Environment Setup
```shell
$ cd <path-to>/superagentx
$ python3.12 -m venv venv
$ source venv/bin/activate
(venv) $ pip install poetry
(venv) $ poetry install
```

## Documentation (_Coming Soon_)

## License

SuperAgentX is released under the [MIT](https://github.com/decisionfacts/superagentX/blob/master/LICENSE) License.

