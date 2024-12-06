from ollama import chat
from config.prompts import SYSTEM_PROMPT, USER_PROMPT_TWITTER


class TweetGeneratorOllama:
    def __init__(self):
        self.system = SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER

    def create_tweet(self, tweets: str) -> str:
        """
        Generate a tweet using the Ollama chat model.

        Args:
            tweets (str): The input text to generate a tweet from
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
                    "content": self.prompt.format(twitter_timeline=tweets),
                },
            ],
            options={
                "temperature": 1.5,
                "num_predict": 720,
                "num_ctx": 16384,
            },
        )
        return response["message"]["content"]
