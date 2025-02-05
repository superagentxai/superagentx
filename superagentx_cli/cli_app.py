import json
from typing import Annotated, Optional

import typer
from superagentx_cli.cli import CliApp

app = typer.Typer(name='Superagentx-App')


@app.command(name='app')
def main(
        app_config_path: Annotated[str, typer.Option(
            help='Application configuration path.'
        )],
        app_dir_path: Annotated[Optional[str], typer.Option(
            help='Application will be created in the given dir path.'
                 ' Default will be current execution path.'
        )] = None
):
    with open(app_config_path, 'r') as fobj:
        app_config = json.load(fobj)
        cli_app = CliApp(
            app_config=app_config,
            app_dir_path=app_dir_path
        )
        cli_app.create_project()

if __name__ == '__main__':
    app()
