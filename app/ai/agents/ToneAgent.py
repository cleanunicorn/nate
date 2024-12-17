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

    def adjust_tone_thread(self, thread: TweetThreadModel) -> TweetThreadModel:
        """
        Adjust the tone of the given content to match the target tone.

        Args:
            content (str): The original content to adjust

        Returns:
            str: The content rewritten in the target tone
        """
        prompt = f"Topic: {thread.topic}\n---\n"
        prompt += "\n---\n".join(tweet.text for tweet in thread.tweets)

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
            temperature=1.2,
            top_p=0.85,
            # frequency_penalty=0.2,
            presence_penalty=0.15,
        )

        parsed_response = response.choices[0].message.parsed

        for i, tweet in enumerate(parsed_response.tweets):
            # Clean tweets
            tweet.text = clean_tweet(tweet.text)

            # Retain quote tweet id
            if len(parsed_response.tweets) == len(thread.tweets):
                parsed_response.tweets[i].quote_tweet_id = thread.tweets[
                    i
                ].quote_tweet_id

        return parsed_response

    def adjust_tone_single_tweet(self, tweet: TweetModel) -> TweetModel:
        """
        Adjust the tone of a single tweet.

        Args:
            tweet (TweetModel): The tweet to adjust

        Returns:
            TweetModel: The tweet rewritten with adjusted tone
        """
        prompt = tweet.text

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": TONE_ADJUSTMENT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format=TweetModel,
            temperature=1.2,
            max_tokens=760,
            top_p=0.85,
            frequency_penalty=0.2,
            presence_penalty=0.15,
        )

        parsed_response = response.choices[0].message.parsed

        # Clean tweet
        parsed_response.text = clean_tweet(parsed_response.text)

        # Retain quote tweet id
        parsed_response.quote_tweet_id = tweet.quote_tweet_id

        return parsed_response
