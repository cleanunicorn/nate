from openai import OpenAI
from config.prompts import SYSTEM_PROMPT, USER_PROMPT_TWITTER


class TweetGeneratorOpenRouter:
    def __init__(self, api_key=None):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def create_tweet(self, tweets: str) -> str:
        """
        Generate a tweet using the Ollama chat model.

        Args:
            tweets (str): The input text to generate a tweet from
        """
        completion = self.client.chat.completions.create(
            model="meta-llama/llama-3.1-405b-instruct",
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
            stream_options={"temperature": 1.8, "max_tokens": 720},
        )

        print(completion)

        return completion.choices[0].message.content
