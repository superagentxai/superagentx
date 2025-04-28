import os.path
import re
import sys
import uuid
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Any

import typer
import yapf.yapflib.yapf_api
from camel_converter import dict_to_snake
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, ValidationError
from rich import print as rprint

from superagentx_cli.exceptions import AppConfigError

PKG_NAME_COMP = re.compile(r'^[A-Za-z][a-zA-Z0-9_ -]*$')
EMAIL_COMP = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def dict_to_kwargs(d: dict) -> list:
    return [
        f'{key}={"'" + val + "'" if isinstance(val, str) else val}' for key, val in d.items()
    ]


def str_to_obj_str(l: list) -> str:
    _l = '['
    for __l in l:
        if isinstance(__l, list):
            _l = _l + str_to_obj_str(__l)
        else:
            _l = _l + to_snake(__l) + ', '
    if _l.endswith(', '):
        _l = _l.rstrip(', ')
    _l = _l + ']'
    return _l


def to_snake(s: str):
    return '_'.join(
        re.sub(
            '([A-Z][a-z]+)', r' \1',
            re.sub(
                '([A-Z]+)', r' \1',
                s.replace('-', ' ')
            )
        ).split()
    ).lower()


class LLM(BaseModel):
    title: str
    llm_config: dict


class Memory(BaseModel):
    title: str
    memory_config: dict


class HandlerConfig(BaseModel):
    title: str
    handler_name: str
    src_path: str
    attributes: dict | None = None


class PromptTemplateConfig(BaseModel):
    title: str
    prompt_type: str | None = None
    system_message: str | None = None


class EngineConfig(BaseModel):
    title: str
    handler: str
    llm: str
    prompt_template: str
    tools: list | None = None
    output_parser: Any | None = None


class AgentConfig(BaseModel):
    title: str
    goal: str
    role: str
    llm: str
    prompt_template: str
    agent_id: str | None = None
    name: str | None = None
    description: str | None = None
    engines: list[str | list[str]]
    output_format: str | None = None
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
    app_type: str  # TODO: Change this with CliAppTypeEnum
    llm: list[LLM]
    memory: list[Memory]
    handler_config: list[HandlerConfig]
    prompt_template_config: list[PromptTemplateConfig]
    engine_config: list[EngineConfig]
    agent_config: list[AgentConfig]
    pipe_config: list[PipeConfig]
    app_auth_token: str | None = None


class AppCreation:

    def __init__(
            self,
            app_config: AppConfig
    ):
        self.app_config = app_config
        self.imports = []
        self.llms = {}
        self.memories = {}
        self.handlers = {}
        self.prompt_templates = {}
        self.engines = {}
        self.agents = {}
        self.pipe = None
        self.pipe_name = None

    def construct(self):
        self._construct_llms()
        self._construct_memories()
        self._construct_handlers()
        self._construct_prompt_templates()
        self._construct_engines()
        self._construct_agents()
        self._construct_pipes()

    def _construct_llms(self):
        for llm in self.app_config.llm:
            title_2_var = to_snake(s=llm.title)
            self.llms[llm.title] = (f"{title_2_var} = LLMClient({
                ', '.join(dict_to_kwargs(llm.model_dump(exclude={'title': True})))
                }"
            f")")
        if self.llms:
            self.imports.append(
                'from superagentx.llm import LLMClient'
            )

    def _construct_memories(self):
        for memory in self.app_config.memory:
            title_2_var = to_snake(memory.title)
            _llm_client = memory.memory_config.get('llm_client')
            if _llm_client:
                _llm_client = to_snake(_llm_client)
            _vector_store = memory.memory_config.get('vector_store')
            if _vector_store:
                _vector_store = to_snake(_vector_store)
            _db_path = memory.memory_config.get('db_path')
            self.memories[memory.title] = (f"{title_2_var} = Memory("
               f"memory_config={{'llm_client': {_llm_client}, 'vector_store': {_vector_store}, 'db_path': {_db_path}}}"
           f")")
        if self.memories:
            self.imports.append(
                'from superagentx.memory import Memory'
            )

    def _construct_handlers(self):
        for handler in self.app_config.handler_config:
            title_2_var = to_snake(handler.title)
            _kwargs = dict_to_kwargs(handler.attributes or {})
            self.handlers[handler.title] = (f"{title_2_var} = {handler.handler_name}("
                f"{', '.join(_kwargs)}"
            f")")
            _h_import = f'from {handler.src_path} import {handler.handler_name}'
            if not _h_import in self.imports:
                self.imports.append(
                    _h_import
                )

    def _construct_prompt_templates(self):
        for prompt_template in self.app_config.prompt_template_config:
            title_2_var = to_snake(prompt_template.title)
            _kwargs = dict_to_kwargs(prompt_template.model_dump(exclude={'title': True}))
            self.prompt_templates[prompt_template.title] = (f"{title_2_var} = PromptTemplate("
                f"{', '.join(_kwargs)}"
            f")")
        if self.prompt_templates:
            self.imports.append(
                'from superagentx.prompt import PromptTemplate'
            )

    def _construct_engines(self):
        for engine in self.app_config.engine_config:
            title_2_var = to_snake(engine.title)
            _handler = to_snake(engine.handler)
            _llm = to_snake(engine.llm)
            _prompt_template = to_snake(engine.prompt_template)
            self.engines[engine.title] = (
                f"{title_2_var} = Engine("
                f"handler={_handler}, llm={_llm},"
                    f" prompt_template={_prompt_template}, tools={engine.tools},"
                    f" output_parser={engine.output_parser}"
                f")"
            )
        if self.engines:
            self.imports.append(
                'from superagentx.engine import Engine'
            )

    def _construct_agents(self):
        for agent in self.app_config.agent_config:
            title_2_var = to_snake(agent.title)
            _llm = to_snake(agent.llm)
            _prompt_template = to_snake(agent.prompt_template)
            _engines = str_to_obj_str(agent.engines)
            _kwargs = dict_to_kwargs(agent.model_dump(
                exclude={'title': True, 'llm': True, 'prompt_template': True, 'engines': True}
            ))
            self.agents[agent.title] = (
                f"{title_2_var} = Agent("
                    f"llm={_llm}, prompt_template={_prompt_template}, "
                    f"engines={_engines}, {', '.join(_kwargs)}"
                f")"
            )
        if self.agents:
            self.imports.append(
                'from superagentx.agent import Agent'
            )

    def _construct_pipes(self):
        pipe = self.app_config.pipe_config[0]
        title_2_var = to_snake(pipe.title)
        _agents = str_to_obj_str(pipe.agents)
        _memory = to_snake(pipe.memory)
        _kwargs = dict_to_kwargs(pipe.model_dump(exclude={'title': True, 'agents': True, 'memory': True}))
        self.pipe = (f"{title_2_var} = AgentXPipe("
             f"agents={_agents}, memory={_memory}, {', '.join(_kwargs)}"
        f")")
        self.imports.append('from superagentx.agentxpipe import AgentXPipe')
        self.pipe_name = title_2_var


class CliAppTypeEnum(str, Enum):
    all = 'all'
    io = 'console'
    ws = 'websocket'
    rest = 'rest'


class CliApp:

    def __init__(
            self,
            name: str | None = None,
            pipe_name: str | None = None,
            app_type: str = CliAppTypeEnum.all.value,
            author_name: str = 'Example Author',
            author_email: str = 'author@example.com',
            maintainer_name: str = 'Example Maintainer',
            maintainer_email: str = 'maintainer@example.com',
            app_config: dict | None = None,
            app_dir_path: str | PathLike | None = None
    ):

        self.app_name = name
        self.app_type = app_type

        self.app_config = None
        if app_config:
            try:
                self.app_config = AppConfig(**dict_to_snake(app_config))
                self.app_name = self.app_config.app_name
                self.app_type = self.app_config.app_type
            except ValidationError as ex:
                raise AppConfigError(ex)

        self.package_name = to_snake(s=self.app_name)
        self.pipe_name = to_snake(s=pipe_name or self.app_name)
        self.author_name = author_name
        self.author_email =author_email
        self.maintainer_name = maintainer_name
        self.maintainer_email = maintainer_email
        _app_dir = Path(app_dir_path) if app_dir_path else Path().cwd()
        self._app_dir = _app_dir / self.app_name
        self._config_dir = self._app_dir / 'config'
        self._pkg_dir = self._app_dir / self.package_name
        self._jinja_env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            )
        )

    def create_pipe_file(self):
        _pipe_path = self._pkg_dir / 'pipe.py'
        rprint(f'Creating pipe file at [yellow]{_pipe_path.resolve()}')
        _pipe_template_file = self._jinja_env.get_template('pipe.py.jinja2')
        _render_pipe = _pipe_template_file.render(
            pipe_name=self.pipe_name
        )
        _pipe_path.write_text(_render_pipe)

    def create_pipe_file_from_app_config(self):
        if not self.app_config:
            raise AppConfigError('Not valida app configuration!')

        app_creation = AppCreation(app_config=self.app_config)
        app_creation.construct()
        self.pipe_name = app_creation.pipe_name
        _pipe_path = self._pkg_dir / 'pipe.py'
        rprint(f'Creating pipe file at [yellow]{_pipe_path.resolve()}')
        _pipe_template_file = self._jinja_env.get_template('app_pipe.py.jinja2')
        _render_pipe = _pipe_template_file.render(
            imports=app_creation.imports,
            pipe_name=self.pipe_name,
            llms=app_creation.llms.values(),
            memories=app_creation.memories.values(),
            handlers=app_creation.handlers.values(),
            prompt_templates=app_creation.prompt_templates.values(),
            engines=app_creation.engines.values(),
            agents=app_creation.agents.values(),
            pipe=app_creation.pipe
        )
        _formatted_code, _ = yapf.yapflib.yapf_api.FormatCode(_render_pipe)
        _pipe_path.write_text(_formatted_code)

    def _create_app_pipe_file(self, app_type: str):
        _app_type_pipe_path = self._pkg_dir / f'{app_type}pipe.py'
        rprint(f'Creating {app_type}pipe file at [yellow]{_app_type_pipe_path}')
        _app_type_pipe_template_file = self._jinja_env.get_template(f'{app_type}pipe.py.jinja2')
        _render_app_type_pipe = _app_type_pipe_template_file.render(
            package_name=self.package_name,
            pipe_name=self.pipe_name,
            app_name=self.app_name
        )
        _app_type_pipe_path.write_text(_render_app_type_pipe)

    def create_console_file(self):
        self._create_app_pipe_file(app_type='io')

    def create_ws_file(self):
        self._create_app_pipe_file(app_type='ws')

    def create_rest_file(self):
        self._create_app_pipe_file(app_type='rest')

    def create_config(
            self,
            auth_token: str
    ):
        _config_path = self._pkg_dir / 'config.py'
        rprint(f'Creating config file at [yellow]{_config_path.resolve()}')
        _config_template_file = self._jinja_env.get_template('config.py.jinja2')
        _render_config = _config_template_file.render(
            auth_token=auth_token
        )
        _config_path.write_text(_render_config)

    def create_all_app_type_file(self):
        self.create_console_file()
        self.create_ws_file()
        self.create_rest_file()

    def create_readme_file(self):
        _readme_path = self._app_dir / 'README.md'
        rprint(f'Creating readme file at [yellow]{_readme_path.resolve()}')
        _readme_template_file = self._jinja_env.get_template('README.md.jinja2')
        _render_readme = _readme_template_file.render(
            app_name=self.app_name
        )
        _readme_path.write_text(_render_readme)

    def create_toml_file(self):
        _toml_path = self._app_dir / 'pyproject.toml'
        rprint(f'Creating toml file at [yellow]{_toml_path.resolve()}')
        _toml_template_file = self._jinja_env.get_template('pyproject.toml.jinja2')
        _render_toml = _toml_template_file.render(
            package_name=self.package_name.replace('_', '-'),
            author_name=self.author_name,
            author_email=self.author_email,
            maintainer_name=self.maintainer_name,
            maintainer_email=self.maintainer_email
        )
        _toml_path.write_text(_render_toml)

    def create_package(self):
        if self._app_dir.exists():
            rprint(
                f'[bold red]Application directory '
                f'[italic bold yellow]`{self._app_dir.resolve()}`[/italic bold yellow] '
                f'already exists![/bold red]'
            )
            sys.exit(1)
        rprint(f'Creating app at [yellow]{self._pkg_dir.parent.resolve()}')
        self._pkg_dir.mkdir(parents=True)
        pkg_init = self._pkg_dir / '__init__.py'
        pkg_init.touch()

    def create_base_pkg(self):
        self.create_package()
        self.create_toml_file()
        self.create_readme_file()
        if self.app_config:
            self.create_pipe_file_from_app_config()
        else:
            self.create_pipe_file()

    def create_project(self):
        rprint(
            f'\nApp Name ✈️ [italic bold yellow]{self.app_name}[/italic bold yellow]\n'
            f'Pacakge Name 📦 [italic bold yellow]{self.package_name}[/italic bold yellow]\n'
            f'Pipe Name 🎢 [italic bold yellow]{self.pipe_name}[/italic bold yellow]\n'
            f'App Type 🛠️ [italic bold yellow]{self.app_type}[/italic bold yellow]\n'
            # f'Author Name 😎 [italic bold yellow]{self.author_name}[/italic bold yellow] '
            # f'Email ✉️ [italic bold yellow]{self.author_email}[/italic bold yellow]\n'
            # f'Maintainer Name 😎 [italic bold yellow]{self.maintainer_name}[/italic bold yellow] '
            # f'Email ✉️ [italic bold yellow]{self.maintainer_email}[/italic bold yellow]\n'
        )
        self.create_base_pkg()

        if self.app_type in (
            CliAppTypeEnum.all.value,
            CliAppTypeEnum.rest.value,
            CliAppTypeEnum.ws.value
        ):
            if self.app_config:
                token = self.app_config.app_auth_token or uuid.uuid4().hex
            else:
                rprint(f'Your app type selection contains `websocket`, `rest api` option(s).\n')
                token = typer.prompt(
                    'Enter auth token for `websocket`, `rest api`',
                    default=uuid.uuid4().hex
                )
            self.create_config(auth_token=token)

        match self.app_type:
            case CliAppTypeEnum.all:
                self.create_all_app_type_file()
            case CliAppTypeEnum.io:
                self.create_console_file()
            case CliAppTypeEnum.ws:
                self.create_ws_file()
            case CliAppTypeEnum.rest:
                self.create_rest_file()
