from openai import OpenAI

from app.ai.models import TweetThreadFormat, TweetFormat
from config.prompts import TONE_ADJUSTMENT_SYSTEM_PROMPT


class ToneAgent:
    """
    A class that uses OpenAI to optimize the tone of voice for content.
    """

    def __init__(self, api_key: str):
        """
        Initialize the ToneAgent.

        Args:
            api_key (str, optional): OpenAI API key. If not provided, will use environment variable.
        """
        self.client = OpenAI(api_key=api_key)

    def adjust_tone_thread(self, content: list[str]) -> TweetThreadFormat:
        """
        Adjust the tone of the given content to match the target tone.

        Args:
            content (str): The original content to adjust

        Returns:
            str: The content rewritten in the target tone
        """
        prompt = "\n---\n".join(content)

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": TONE_ADJUSTMENT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            response_format=TweetThreadFormat,
        )

        return response.choices[0].message.parsed

    def adjust_tone_single_tweet(self, content: str) -> TweetFormat:
        """
        Adjust the tone of a single tweet.

        Args:
            content (str): The original tweet content to adjust

        Returns:
            TweetFormat: The tweet rewritten with adjusted tone
        """
        prompt = content

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": TONE_ADJUSTMENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=TweetFormat,
        )

        return response.choices[0].message.parsed
