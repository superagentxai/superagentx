import json
import os.path

with open(os.path.join(os.path.dirname(__file__), 'cli_app.json'), 'rb') as fobj:
    d = json.load(fobj)

from superagentx_cli.cli import CliApp


def main():
    cli_app = CliApp(app_config=d)
    print(cli_app.render_pipe())
    cli_app.create_project()


if __name__ == '__main__':
    main()
