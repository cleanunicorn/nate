import requests
import json
import time

from pydantic import BaseModel


from config.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TWITTER,
    TWITTER_PROMPT_SINGLE_TWEET,
    TWITTER_PROMPT_THREAD,
)
from app.utils.utils import format_tweet_timeline

class TweetThreadFormat(BaseModel):
    tweets: list[str]
    topic: str

class TweetFormat(BaseModel):
    text: str
    topic: str

class TweetGeneratorOpenRouter:
    def __init__(self, api_key=None):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER
        self.api_key = api_key

    def create_message(self, messages, thread: bool = False) -> str:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
            data=json.dumps(
                {
                    "model": "meta-llama/llama-3.3-70b-instruct",
                    "messages": messages,
                    "temperature": 1.2,
                    "seed": int(time.time()),
                    "max_tokens": 720,
                    # TODO: It's not working with structured_output/response_format
                    # "structured_output": TweetThreadFormat.model_json_schema() if thread else TweetFormat.model_json_schema(),
                }
            ),
            timeout=10,
        )

        # Check if the request was successful
        response.raise_for_status()

        # TODO: It's not working with structured_output/response_format
        # if thread:
        #     content = TweetThreadFormat.model_validate_json(response.json())
        # else:
        #     content = TweetFormat.model_validate_json(response.json())

        # Parse the JSON response
        response_data = response.json()

        # Check if we have valid choices in the response
        if not response_data.get("choices") or len(response_data["choices"]) == 0:
            raise ValueError("No completion choices found in the response")

        # Extract the generated text from the first choice
        # The message content is where the actual response text is stored
        first_choice = response_data["choices"][0]
        if "message" in first_choice and "content" in first_choice["message"]:
            return first_choice["message"]["content"]
        else:
            raise ValueError("Unexpected response format")

    def create_tweet(self, tweets: str, thread: bool = False) -> str:
        """
        Generate a tweet using the Ollama chat model.

        Args:
            tweets (str): The input text to generate a tweet from
        """
        messages = [
            {
                "role": "system",
                "content": self.system,
            },
            {
                "role": "user",
                "content": self.prompt.format(
                    twitter_timeline=format_tweet_timeline(tweets),
                    twitter_action=TWITTER_PROMPT_SINGLE_TWEET if not thread else TWITTER_PROMPT_THREAD
                ),
            },
        ]
        completion = self.create_message(
            messages=messages,
            thread=thread,
        )

        if thread:
            return TweetThreadFormat(
                tweets=completion.split("\n"),
                topic="",
            )
        else:
            return TweetFormat(
                text=completion,
                topic=completion.split("\n")[0],
            )
