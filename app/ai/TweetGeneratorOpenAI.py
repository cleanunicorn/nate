from openai import OpenAI
from typing import List, Dict
import time

from config.prompts import SYSTEM_PROMPT, USER_PROMPT_TWITTER
from app.utils.utils import format_tweet_timeline


class TweetGeneratorOpenAI:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER

    def create_message(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=1.1,
            # seed=int(time.time()),
            max_tokens=720,
            top_p=0.85,
            frequency_penalty=0.15,
            presence_penalty=0.25,
        )

        if not response.choices:
            raise ValueError("No completion choices found in the response")

        return response.choices[0].message.content

    def create_tweet(self, tweets: str) -> str:
        """
        Generate a tweet using the OpenAI chat model.

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
                    twitter_timeline=format_tweet_timeline(tweets)
                ),
            },
        ]

        completion = self.create_message(messages=messages)

        print(messages)

        return completion
