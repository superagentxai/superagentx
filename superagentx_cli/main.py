import os.path
import re
import sys
import uuid
from enum import Enum
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader
from rich import print as rprint

PKG_NAME_COMP = re.compile(r'^[A-Za-z][a-zA-Z0-9_ -]*$')
EMAIL_COMP = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


class CliAppTypeEnum(str, Enum):
    all = 'all'
    io = 'console'
    ws = 'websocket'
    rest = 'rest'


class CliApp:

    def __init__(
            self,
            name: str,
            pipe_name: str,
            app_type: str,
            author_name: str = 'Example Author',
            author_email: str = 'author@example.com',
            maintainer_name: str = 'Example Maintainer',
            maintainer_email: str = 'maintainer@example.com'
    ):
        self.app_name = name
        self.app_type = app_type
        self.package_name = self.to_snake(s=name)
        self.pipe_name = self.to_snake(s=pipe_name)
        self.author_name = author_name
        self.author_email =author_email
        self.maintainer_name = maintainer_name
        self.maintainer_email = maintainer_email
        self._app_dir = Path().cwd() / self.app_name
        self._config_dir = self._app_dir / 'config'
        self._pkg_dir = self._app_dir / self.package_name
        self._jinja_env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            )
        )

    @staticmethod
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

    def create_pipe_file(self):
        _pipe_path = self._pkg_dir / 'pipe.py'
        rprint(f'Creating pipe file at [yellow]{_pipe_path.resolve()}')
        _pipe_template_file = self._jinja_env.get_template('pipe.py.jinja2')
        _render_pipe = _pipe_template_file.render(
            pipe_name=self.pipe_name
        )
        _pipe_path.write_text(_render_pipe)

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


app = typer.Typer(name='Superagentx-Cli')


def validate_email(email: str) -> str:
    if email and not bool(EMAIL_COMP.match(email)):
        raise typer.BadParameter('Invalid email!')
    return email


def validate_project_name(name: str) -> str:
    if name and not bool(PKG_NAME_COMP.match(name)):
        raise typer.BadParameter('Starts with alphabets along with numbers, `-` and `_`')
    return name


@app.command(name='help')
def cli_help():
    rprint(f"Superagentx cli to create project structures based on the options.")


@app.command(name='create')
def create(
        name: str = typer.Option(
            prompt='Enter application name',
            help='Name of the application. '
                 'It helps to create application dir and pacakge in the given name. '
                 'Starts with alphabets along with numbers, `-` and `_`',
            rich_help_panel='Application Name',
            callback=validate_project_name
        ),
        pipe_name: str = typer.Option(
            default='',
            prompt='Enter pipe name. Default is application name',
            rich_help_panel='Pipe Name',
            callback=validate_project_name
        ),
        app_type: CliAppTypeEnum = typer.Option(
            CliAppTypeEnum.all.value,
            prompt='Enter one of the option',
            rich_help_panel='App Types'
        )
):
    cli_app = CliApp(
        name=name,
        pipe_name=pipe_name or name,
        app_type=app_type.value
    )
    cli_app.create_project()


if __name__ == '__main__':
    app()
