import json
import sys
from typing import Annotated, Optional

import typer
from superagentx_cli.cli import CliApp
from superagentx_cli.exceptions import AppConfigError

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
        try:
            cli_app = CliApp(
                app_config=app_config,
                app_dir_path=app_dir_path
            )
            cli_app.create_project()
        except (AppConfigError, Exception) as ex:
            sys.stderr(f"Superagentx app creation failed!\n{ex}")
            sys.exit(1)

if __name__ == '__main__':
    app()
