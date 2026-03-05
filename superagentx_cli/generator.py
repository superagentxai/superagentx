from enum import Enum
import os
import re
from typing import List, Optional, Any

from jinja2 import Environment
from pydantic import BaseModel


# ==========================================================
# Utilities
# ==========================================================

def to_snake(s):
    if not isinstance(s, str):
        return s
    return '_'.join(
        re.sub(
            '([A-Z][a-z]+)', r' \1',
            re.sub(
                '([A-Z]+)', r' \1',
                s.replace('-', ' ')
            )
        ).split()
    ).lower()


def dict_to_snake(data: dict) -> dict:
    converted = {}
    for k, v in data.items():
        key = k if k.isupper() else to_snake(k) if isinstance(k, str) else k

        if isinstance(v, dict):
            converted[key] = dict_to_snake(v)
        elif isinstance(v, list):
            converted[key] = [dict_to_snake(i) if isinstance(i, dict) else i for i in v]
        else:
            converted[key] = v
    return converted


def list_to_snake_obj(value):
    """
    Converts:
        ["A", ["B", "C"]]
    into:
        [a, [b, c]]
    """
    if isinstance(value, list):
        return "[" + ", ".join(list_to_snake_obj(v) for v in value) + "]"
    else:
        return to_snake(value)


# ==========================================================
# Models
# ==========================================================

class LLM(BaseModel):
    title: str
    llm_config: dict


class HandlerConfig(BaseModel):
    title: str
    handler_name: str
    src_path: str
    attributes: dict | None = None


class PromptTemplateConfig(BaseModel):
    title: str
    prompt_type: str | None = None
    system_message: str | None = None

class EngineType(Enum):
    browser = "BROWSER"
    task = "TASK"
    default = "DEFAULT"

class EngineConfig(BaseModel):
    title: str
    handler: str | None = None
    llm: str | None = None
    prompt_template: str | None = None
    tools: list | None = None
    output_parser: Any | None = None
    engine_type: str | Enum | None = None
    instructions: List[Any] | None = None
    browser_engine_config: dict | None = None
    task_engine_config: dict | None = None

class AgentConfig(BaseModel):
    title: str
    goal: str | None = None
    role: str | None = None
    llm: str | None = None
    prompt_template: str | None = None
    agent_id: str | None = None
    name: str | None = None
    tool: str | None = None
    description: str | None = None
    engines: List[Any] | None = None
    output_format: str | None = None
    human_approval: bool = False
    agents_config: dict | None = None
    max_retry: int = 5


class PipeConfig(BaseModel):
    title: str
    pipe_id: str | None = None
    name: str | None = None
    description: str | None = None
    agents: list[str | list[str]]
    memory: str | None = None
    stop_if_goal_not_satisfied: bool = False

class AppConfig(BaseModel):
    app_name: str
    app_type: str
    llm_config: dict[Any, Any] | None = None
    prompt_template: str | None = None
    llm: list[LLM] | None = None
    memory: list[dict] | None = None
    handler_config: list[HandlerConfig] | None = None
    prompt_template_config: list[PromptTemplateConfig] | None = None
    engine_config: list[EngineConfig] | None = None
    agent_config: list[AgentConfig] | None = None
    pipe_config: list[PipeConfig]
    app_auth_token: str | None = None


# ==========================================================
# Embedded Template
# ==========================================================

APP_TEMPLATE = """
{%- for import in imports %}
{{ import }}
{%- endfor %}

{%- if load_dotenv %}
load_dotenv()
{%- endif %}

async def get_{{ pipe_name }}_pipe() -> AgentXPipe:
    # LLM Configuration
    {%- for llm in llms %}
    {{ llm | indent(4)}}
    {%- endfor %}

    # Prompt Templates
    {%- for prompt in prompts %}
    {{ prompt }}
    {%- endfor %}

    # Handlers
    {%- for handler in handlers %}
    {{ handler }}
    {%- endfor %}

    # Engines
    {%- for engine in engines %}
    {{ engine }}
    {%- endfor %}

    # Agents
    {%- for agent in agents %}
    {{ agent }}
    {%- endfor %}

    # Pipe
    {{ pipe }}

    return {{ pipe_name }}

get_pipe = get_{{ pipe_name }}_pipe
"""


# ==========================================================
# Compiler
# ==========================================================

class SuperAgentXCompiler:

    def __init__(self, config: AppConfig):
        self.config = config
        self.imports = []
        self.llms = {}
        self.prompts = {}
        self.handlers = {}
        self.engines = {}
        self.agents = {}
        self.env_vars = {}
        self.pipe = None
        self.pipe_name = None

    # ---------------- LLM ----------------

    def build_llms(self):
        if not self.config.llm:
            return

        for llm in self.config.llm:
            var = to_snake(llm.title)
            llm_config_copy = dict(llm.llm_config)

            llm_type = llm_config_copy.get("llm_type") or llm_config_copy.get("llmType")
            model = llm_config_copy.get("model", "")
            api_key = llm_config_copy.get("api_key") or llm_config_copy.get("apiKey")

            provider = self.detect_provider(llm.title, str(llm_type), str(model))

            if provider and api_key:
                env_name = f"{provider}_API_KEY"
                self.env_vars[env_name] = api_key
                llm_config_copy["api_key"] = f'os.getenv("{env_name}")'
                llm_config_copy.pop("apiKey", None)

            config_lines = []
            for k, v in llm_config_copy.items():
                if v is None:
                    continue
                if isinstance(v, str) and v.startswith("os.getenv"):
                    config_lines.append(f'"{k}": {v}')
                elif isinstance(v, str):
                    config_lines.append(f'"{k}": "{v}"')
                else:
                    config_lines.append(f'"{k}": {v}')

            block = ",\n    ".join(config_lines)

            self.llms[llm.title] = (
                f"{var}_config = {{\n"
                f"    {block}\n"
                f"}}\n\n"
                f"{var} = LLMClient(llm_config={var}_config)"
            )

        if self.llms:
            self.imports.append("from superagentx.llm import LLMClient")

    def detect_provider(self, title: str, llm_type: str, model: str) -> Optional[str]:
        combined = f"{title} {llm_type} {model}".lower()

        if "gemini" in combined:
            return "GEMINI"
        if "openai" in combined and "azure" not in combined:
            return "OPENAI"
        if "anthropic" in combined or "claude" in combined:
            return "ANTHROPIC"
        if "xai" in combined:
            return "XAI"
        if "huggingface" in combined:
            return "HUGGINGFACE"
        if "openrouter" in combined:
            return "OPENROUTER"
        if "nvidia" in combined or "nim" in combined:
            return "NVIDIA"
        if "azure" in combined:
            return "AZURE"
        if "vertex" in combined:
            return "VERTEX"

        return None

    # ---------------- Prompts ----------------

    def build_prompts(self):
        if not self.config.prompt_template_config:
            return

        for prompt in self.config.prompt_template_config:
            var = to_snake(prompt.title)

            self.prompts[prompt.title] = f"""{var} = PromptTemplate(
        prompt_type={repr(prompt.prompt_type)},
        system_message={repr(prompt.system_message)}
    )
"""

        if self.prompts:
            self.imports.append("from superagentx.prompt import PromptTemplate")

    # ---------------- Handlers ----------------

    def build_handlers(self):
        if not self.config.handler_config:
            return

        for handler in self.config.handler_config:
            var = to_snake(handler.title)

            kwargs = []
            for k, v in (handler.attributes or {}).items():
                if isinstance(v, str) and v in self.llms:
                    kwargs.append(f"{k}={to_snake(v)}")
                elif isinstance(v, str):
                    kwargs.append(f'{k}="{v}"')
                else:
                    kwargs.append(f"{k}={v}")

            self.handlers[handler.title] = f"{var} = {handler.handler_name}({', '.join(kwargs)})"

            self.imports.append(f"from {handler.src_path} import {handler.handler_name}")

    # ---------------- Engines ----------------

    def build_engines(self):
        if not self.config.engine_config:
            return

        for engine in self.config.engine_config:
            var = to_snake(engine.title)

            if engine.prompt_template:
                prompt_template_code = f'PromptTemplate(system_message={repr(engine.prompt_template)})'
            else:
                prompt_template_code = 'PromptTemplate()'

            if engine.engine_type:
                engine_type = engine.engine_type.upper()

                # Task Agent
                if engine_type == EngineType.task.value:
                    _handler = to_snake(engine.handler)
                    self.engines[engine.title] = f"""{var} = TaskEngine(
                           handler={_handler}, instructions={engine.instructions}
                       )"""
                    if engine.task_engine_config:
                        self.engines[engine.title] = f"""{var} = TaskEngine(
                               handler={_handler}, instructions={engine.instructions},
                               **{engine.task_engine_config}
                           )"""
                    if 'from superagentx.task_engine import TaskEngine' not in self.imports:
                        self.imports.append(
                            'from superagentx.task_engine import TaskEngine'
                        )
                # Browser Agent
                elif engine.engine_type == EngineType.browser.value:
                    _llm = to_snake(engine.llm)
                    _prompt_template = to_snake(engine.prompt_template)
                    self.engines[engine.title] = f"""{var} = BrowserEngine(
                           llm={_llm}, prompt_template={prompt_template_code},
                       )"""
                    if engine.browser_engine_config:
                        self.engines[engine.title] = f"""{var} = BrowserEngine(
                               llm={_llm}, prompt_template={_prompt_template},
                               **{engine.browser_engine_config}
                           )"""
                    if 'from superagentx.browser_engine import BrowserEngine' not in self.imports:
                        self.imports.append(
                            'from superagentx.browser_engine import BrowserEngine'
                        )
            else:
                self.engines[engine.title] = f"""{var} = Engine(
                       handler={to_snake(engine.handler)},
                       llm={to_snake(engine.llm)},
                       prompt_template={prompt_template_code},
                       tools={engine.tools},
                       output_parser={engine.output_parser}
                   )"""
                if self.engines:
                    self.imports.append("from superagentx.engine import Engine")

    # ---------------- Agents ----------------

    def build_agents(self):
        if not self.config.agent_config:
            return

        for agent in self.config.agent_config:
            var = to_snake(agent.title)
            engines_list = list_to_snake_obj(agent.engines)

            if agent.prompt_template:
                prompt_template_code = f'PromptTemplate(system_message={repr(agent.prompt_template)})'
            else:
                prompt_template_code = 'PromptTemplate()'

            self.agents[agent.title] = f"""{var} = Agent(
        llm={to_snake(agent.llm)},
        prompt_template={prompt_template_code},
        engines={engines_list},
        goal={repr(agent.goal)},
        tool={to_snake(agent.tool)},
        role={repr(agent.role)},
        agent_id={repr(agent.agent_id)},
        name={repr(agent.name)},
        description={repr(agent.description)},
        human_approval={repr(agent.human_approval)},
        output_format={repr(agent.output_format)},
        max_retry={agent.max_retry}
    )
"""
        if self.agents:
            self.imports.append("from superagentx.agent import Agent")
            self.imports.append("from superagentx.prompt import PromptTemplate")

    # ---------------- Pipe ----------------

    def build_pipe(self):
        if not self.config.pipe_config:
            return

        pipe: PipeConfig = self.config.pipe_config[0]

        if not pipe:
            return

        self.pipe_name = to_snake(pipe.title)

        agents_list = list_to_snake_obj(pipe.agents)

        self.pipe = f"""{self.pipe_name} = AgentXPipe(
        agents={agents_list},
        memory={pipe.memory or []},
        pipe_id={repr(pipe.pipe_id)},
        name={repr(pipe.name)},
        description={repr(pipe.description)},
        stop_if_goal_not_satisfied={pipe.stop_if_goal_not_satisfied}
    )"""

        self.imports.append("from superagentx.agentxpipe import AgentXPipe")

    # ---------------- ENV FILE (SAFE) ----------------

    def generate_env_file(self, path=".env"):
        if not self.env_vars:
            return

        if os.path.exists(path):
            print(f" {path} already exists. Skipping generation.")
            return

        with open(path, "w") as f:
            for k, v in self.env_vars.items():
                safe_val = v.replace('"', '\\"')
                f.write(f'{k}="{safe_val}"\n')

        print(f" .env generated at {path}")

    # ---------------- Render ----------------

    def render(self):
        self.build_llms()
        self.build_prompts()
        self.build_handlers()
        self.build_engines()
        self.build_agents()
        self.build_pipe()

        load_dotenv = False

        if self.env_vars:
            self.imports.insert(0, "from dotenv import load_dotenv")
            self.imports.insert(1, "import os")
            load_dotenv = True

        env = Environment()
        template = env.from_string(APP_TEMPLATE)
        self.generate_env_file(".env")
        return template.render(
            imports=list(dict.fromkeys(self.imports)),
            pipe_name=self.pipe_name,
            llms=self.llms.values(),
            prompts=self.prompts.values(),
            handlers=self.handlers.values(),
            engines=self.engines.values(),
            agents=self.agents.values(),
            pipe=self.pipe,
            load_dotenv=load_dotenv
        )


# ==========================================================
# CLI ENTRY
# ==========================================================

# if __name__ == "__main__":
#
#     if len(sys.argv) < 2:
#         print("Usage: python superagentx_compiler.py config.json")
#         sys.exit(1)
#
#     with open(sys.argv[1], "r") as f:
#         raw = json.load(f)
#
#     config_dict = dict_to_snake(raw["app_config"])
#     app_config = AppConfig(**config_dict)
#
#     compiler = SuperAgentXCompiler(app_config)
#     result = compiler.render()
#
#     print(result)
