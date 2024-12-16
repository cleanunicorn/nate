from openai import OpenAI

# Group app imports together
from app.ai.models import TweetThreadModel, TweetModel
from app.utils.utils import clean_tweet
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

    def adjust_tone_thread(self, content: TweetThreadModel) -> TweetThreadModel:
        """
        Adjust the tone of the given content to match the target tone.

        Args:
            content (str): The original content to adjust

        Returns:
            str: The content rewritten in the target tone
        """
        prompt = f"Topic: {content.topic}\n---\n"
        prompt += "\n---\n".join(tweet.text for tweet in content.tweets)

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": TONE_ADJUSTMENT_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
            response_format=TweetThreadModel,
        )

        parsed_response = response.choices[0].message.parsed

        # Clean tweets
        for tweet in parsed_response.tweets:
            tweet.text = clean_tweet(tweet.text)

        return parsed_response

    def adjust_tone_single_tweet(self, content: TweetModel) -> TweetModel:
        """
        Adjust the tone of a single tweet.

        Args:
            content (str): The original tweet content to adjust

        Returns:
            TweetModel: The tweet rewritten with adjusted tone
        """
        prompt = content.text

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": TONE_ADJUSTMENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=TweetModel,
        )

        parsed_response = response.choices[0].message.parsed

        # Clean tweet
        parsed_response.text = clean_tweet(parsed_response.text)

        return parsed_response
