
import typer
from rich import print as rprint

from superagentx_cli.cli import EMAIL_COMP, PKG_NAME_COMP, CliAppTypeEnum, CliApp

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
            default=CliAppTypeEnum.all.value,
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
