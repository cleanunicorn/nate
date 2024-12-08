import requests
import json
import time

from config.prompts import SYSTEM_PROMPT, USER_PROMPT_TWITTER


class TweetGeneratorOpenRouter:
    def __init__(self, api_key=None):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER

        self.api_key = api_key

    def create_message(self, messages) -> str:
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
                }
            ),
            timeout=10,
        )

        # Check if the request was successful
        response.raise_for_status()

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

    def create_tweet(self, tweets: str) -> str:
        """
        Generate a tweet using the Ollama chat model.

        Args:
            tweets (str): The input text to generate a tweet from
        """
        completion = self.create_message(
            messages=[
                {
                    "role": "system",
                    "content": self.system,
                },
                {
                    "role": "user",
                    "content": self.prompt.format(twitter_timeline=tweets),
                },
            ],
        )

        return completion
