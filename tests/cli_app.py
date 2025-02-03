d = {
    "appName": "Sample Ecom",
    "appType": "all",
    "appAuthToken": None,
    "llm": [
        {
            "title": "LLM-1",
            "llmConfig": {
                "llmType": "bedrock",
                "model": "bedrock",
                "apiKey": "string",
                "baseUrl": "string",
                "apiVersion": "string",
                "asyncMode": True,
                "embedModel": "string"
            }
        }
    ],
    "memory": [
        {
            "title": "memory-1",
            "memoryConfig": {
                "llmClient": "llm-1",
                "vectorStore": "string",
                "dbPath": "string"
            }
        }
    ],
    "handlerConfig": [
        {
            "title": "Handler-1",
            "handlerName": "AIHandler",
            "attributes": {},
            "srcPath": "superagentx.handler"
        }
    ],
    "promptTemplateConfig": [
        {
            "title": "prompt 1",
            "promptType": None,
            "systemMessage": None
        }
    ],
    "engineConfig": [
        {
            "title": "Engine 1",
            "handler": "Handler-1",
            "llm": "LLM-1",
            "promptTemplate": "prompt 1",
            "tools": None,
            "outputParser": None
        }
    ],
    "agentConfig": [
        {
            "title": "Agent 1",
            "goal": "string",
            "role": "string",
            "llm": "LLM-1",
            "promptTemplate": "prompt 1",
            "agentId": None,
            "name": None,
            "description": "string",
            "engines": ["Engine 1"],
            "outputFormat": None,
            "maxRetry": 2
        }
    ],
    "pipeConfig": [
        {
            "title": "Sample Ecom 1",
            "pipeId": None,
            "name": "Agent Pipe 1",
            "description": "string",
            "agents": ["Agent 1"],
            "memory": "memory-1",
            "stopIfGoalIsNotSatisfied": True
        }
    ]
}

from superagentx_cli.cli import CliApp


def main():
    cli_app = CliApp(app_config=d)
    cli_app.create_project()


if __name__ == '__main__':
    main()
