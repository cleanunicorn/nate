from ollama import chat
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

class TweetGeneratorOllama:
    def __init__(self):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER

    def create_tweet(self, tweets: str, thread: bool = False) -> str:
        """
        Generate a tweet or thread using the Ollama chat model.

        Args:
            tweets (str): The input text to generate from
            thread (bool): Whether to generate a thread instead of single tweet
        """
        response = chat(
            model="llama3.1",
            messages=[
                {
                    "role": "system",
                    "content": self.system,
                },
                {
                    "role": "user",
                    "content": self.prompt.format(
                        twitter_timeline=format_tweet_timeline(tweets),
                        twitter_action=TWITTER_PROMPT_THREAD
                        if thread
                        else TWITTER_PROMPT_SINGLE_TWEET,
                    ),
                },
            ],
            options={
                "temperature": 1.8,
                "num_predict": 720,
                "num_ctx": 16384,
                "seed": 1234,
            },
            format=TweetThreadFormat.model_json_schema() if thread else TweetFormat.model_json_schema(),
        )

        print(response)

        # Extract the tweets from the response
        if thread:
            content = TweetThreadFormat.model_validate_json(response["message"]["content"])
        else:
            content = TweetFormat.model_validate_json(response["message"]["content"])

        return content

    def create_thread(self, tweets):
        """Generate a thread of tweets based on timeline analysis"""
        # Use the same logic as create_tweet but ask for a thread

        response = self.create_tweet(tweets=tweets, thread=True)

        return response
