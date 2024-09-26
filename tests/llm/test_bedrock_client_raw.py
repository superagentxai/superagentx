import boto3
from botocore.exceptions import ClientError
import os

client = boto3.client(
            "bedrock-runtime",
            region_name=os.environ.get("AWS_REGION"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"),
        )

# Set the model ID, e.g., Claude 3 Haiku.
model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"


# Start a conversation with the user message.
user_message = "What is the most famous song on ABCD?"
conversation = [
    {
        "role": "user",
        "content": [{"text": user_message}],
    }
]


tools = [
        {
            "toolSpec": {
                "name": "top_song",
                "description": "Get the most popular song played on a radio station.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "sign": {
                                "type": "string",
                                "description": "The call sign for the radio station for which you want the most "
                                               "popular song. Example calls signs are WZPZ, ABCD and WKRP."
                            }
                        },
                        "required": [
                            "sign"
                        ]
                    }
                }
            }
        }
    ]


try:

    tools_config = {"tools": tools}

    # Send the message to the model, using a basic inference configuration.
    response = client.converse(
        modelId=model_id,
        messages=conversation,
        inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
        toolConfig=tools_config
    )

    # Extract and print the response text.
    response_text = response["output"]["message"]["content"][0]["text"]
    print(response)

except (ClientError, Exception) as e:
    print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
    exit(1)
