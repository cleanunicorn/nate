from openai import OpenAI

from app.ai.models import TweetModel, TweetThreadModel
from config.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TWITTER,
    TWITTER_PROMPT_SINGLE_TWEET,
    TWITTER_PROMPT_THREAD,
)
from app.utils.utils import format_tweet_timeline


class TweetGeneratorOpenAI:
    def __init__(self, api_key: str):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER
        self.client = OpenAI(api_key=api_key)

    def create_tweet(
        self, timeline: list[dict], thread: bool = False
    ) -> TweetModel | TweetThreadModel:
        
        messages=[
            {"role": "system", "content": self.system},
            {
                "role": "user",
                "content": self.prompt.format(
                    twitter_timeline=format_tweet_timeline(timeline),
                    twitter_action=TWITTER_PROMPT_THREAD
                    if thread
                    else TWITTER_PROMPT_SINGLE_TWEET,
                ),
            },
        ]

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=TweetThreadModel if thread else TweetModel,
        )

        content = response.choices[0].message.parsed
        return content

    def create_thread(self, timeline: list[dict]) -> TweetThreadModel:
        return self.create_tweet(timeline=timeline, thread=True)
