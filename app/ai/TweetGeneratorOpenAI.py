from openai import OpenAI

from app.ai.models import TweetFormat, TweetThreadFormat
from config.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TWITTER,
    TWITTER_PROMPT_SINGLE_TWEET,
    TWITTER_PROMPT_THREAD,
    TWITTER_PROMPT_REPLY,
)
from app.utils.utils import format_tweet_timeline


class TweetGeneratorOpenAI:
    def __init__(self, api_key: str):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER
        self.client = OpenAI(api_key=api_key)

    def create_tweet(
        self, tweets: str, thread: bool = False, conversation: str = None,
    ) -> TweetFormat | TweetThreadFormat:
        conversation_section = f"Current Conversation:\n```{conversation}```" if conversation else ""
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system},
                {
                    "role": "user",
                    "content": self.prompt.format(
                        twitter_timeline=format_tweet_timeline(tweets),
                        current_conversation_section=conversation_section,
                        twitter_action=TWITTER_PROMPT_REPLY if conversation 
                        else TWITTER_PROMPT_THREAD if thread 
                        else TWITTER_PROMPT_SINGLE_TWEET,
                    ),
                },
            ],
            response_format=TweetThreadFormat if thread else TweetFormat,
        )

        content = response.choices[0].message.parsed
        return content

    def create_thread(self, tweets: str) -> TweetThreadFormat:
        return self.create_tweet(tweets=tweets, thread=True)
    
    def create_reply(self, tweets: str, conversation: str) -> TweetFormat:
        return self.create_tweet(tweets=tweets, conversation=conversation)
