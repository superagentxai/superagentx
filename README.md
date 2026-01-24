<div align="center">

<img src="https://github.com/superagentxai/superagentX/blob/master/docs/images/fulllogo_transparent.png" width="350">


<br/>


**SuperAgentX**: is an open-source, modular agentic AI framework that enables AI agents to plan, act, and execute real-world workflows—with built-in human approval, governance, and auditability.
Unlike traditional chatbots, SuperAgentX is designed for action, not just conversation.



<br/>

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/release/python-31210/)
[![GitHub Repo stars](https://img.shields.io/github/stars/superagentxai/superagentX)](https://github.com/superagentxai/superagentX)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/superagentxai/superagentX/blob/master/LICENSE)

</div>

## ✨ Why SuperAgentX?

SuperAgentX enables AI agents to:
- Execute multi-step workflows
- Interact with browsers, APIs, databases, tools & MCPs
- Pause for **human approval** before sensitive actions
- Persist execution state, memory, and audit logs

All while keeping humans firmly in control.

# Quick start

```shell
pip install superagentx
```

## 🧠 Core Capabilities

### 🔹 Massive Model & Tool Support
- ✅ **100+ LLMs supported** (OpenAI, Azure OpenAI, Gemini, Claude, Bedrock, OSS models)
- ✅ **10,000+ MCP (Model Context Protocol) tools supported**
- ✅ **Browser Agents** using real browser automation (Playwright)

---

### 🔹 Agentic AI (Beyond Chatbots)
Agents can:
- Understand goals
- Plan execution steps
- Call tools dynamically
- Run sequential or parallel workflows
- Retry, reflect, and recover

---

### 🔹 Human-in-the-Loop Governance
A built-in **Human Approval Governance Agent**:
- Pauses sensitive actions
- Requests explicit approval
- Resumes or aborts execution
- Persists decisions for audit

➡️ AI **cannot act blindly**.

---

## 🗄️ Persistent Data Store & Memory

### Supported Data Stores
- 🗃 **SQLite** – lightweight, local workflows
- 🗄 **PostgreSQL** – production-grade, multi-tenant systems

### Stored Data
- Workflow state
- Agent decisions
- Human approvals
- Tool outputs
- Audit logs
- Context & memory snapshots

---

## 🧩 Example: AI Food Ordering with Approval
1. Plan order
2. Calculate total
3. Generate checkout summary
4. **Pause for approval**
5. Browser agent completes checkout
6. Persist confirmation & logs

<img src="assets/human-approval.png" title="SuperAgentX Architecture"/>

## Browser AI Agent

#### Install Playwright for Browser AI Automation
```bash
pip install playwright
```

```bash
playwright install
```

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
<img src="https://github.com/superagentxai/superagentx/blob/master/assets/superagentx_browser.gif" title="Browser Engine"/>


## Key Features

🚀 **Open-Source Framework**: A lightweight, open-source AI framework built for multi-agent applications with Artificial General Intelligence (AGI) capabilities.

🎯 **Goal-Oriented Multi-Agents**: This technology enables the creation of agents with retry mechanisms to achieve set goals. Communication between agents is Parallel, Sequential, or hybrid.

🏖️ **Easy Deployment**: Offers WebSocket, RESTful API, and IO console interfaces for rapid setup of agent-based AI solutions.

♨️ **Streamlined Architecture**: Enterprise-ready scalable and pluggable architecture. No major dependencies; built independently!

📚 **Contextual Memory**: Uses SQL + Vector databases to store and retrieve user-specific context effectively.

🧠 **Flexible LLM Configuration**: Supports simple configuration options of various Gen AI models.

🤝 **Extendable Handlers**: Allows integration with diverse APIs, databases, data warehouses, data lakes, IoT streams, and more, making them accessible for function-calling features.

💎 **Agentic RPA (Robotic Process Automation)** – SuperAgentX enables computer-use automation for both browser-based and desktop applications, making it an ideal solution for enterprises looking to streamline operations, reduce manual effort, and boost productivity.


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

## 🤝 Contributing
Fork → Branch → Commit → Pull Request  
Keep contributions modular and documented.

## 📬 Connect
- 🌐 https://www.superagentx.ai
- 💻 https://github.com/superagentxai/superagentx

⭐ Star the repo and join the community!
