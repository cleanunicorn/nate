from openai import OpenAI

# Group app imports together
from app.ai.models import TweetThreadModel, TweetModel
from app.utils.utils import clean_tweet
from config.prompts import CRYPTO_MARKET_ANALYSIS_FORMAT_THREAD_PROMPT, CRYPTO_MARKET_ANALYSIS_FORMAT_TWEET_PROMPT, TONE_ADJUSTMENT_SYSTEM_PROMPT


class CryptoMarketAnalysisFormatAgent:
    """
    A class that uses OpenAI to format the content.
    """

    def __init__(self, api_key: str):
        """
        Initialize the CryptoMarketAnalysisFormatAgent.

        Args:
            api_key (str, optional): OpenAI API key. If not provided, will use environment variable.
        """
        self.client = OpenAI(api_key=api_key)
        self.crypto_market_analysis_format_thread_system_prompt = CRYPTO_MARKET_ANALYSIS_FORMAT_THREAD_PROMPT
        self.crypto_market_analysis_format_tweet_system_prompt = CRYPTO_MARKET_ANALYSIS_FORMAT_TWEET_PROMPT


    def format_thread(self, thread: TweetThreadModel) -> TweetThreadModel:
        """
        Adjust the format of the given thread accordingly.

        Args:
            content (str): The original content to format

        Returns:
            str: The content formatted accordingly
        """
        prompt = f"Topic: {thread.topic}\n---\n"
        prompt += "\n---\n".join(tweet.text for tweet in thread.tweets)

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": self.crypto_market_analysis_format_thread_system_prompt,
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
            # Format tweet
            self.format_single_tweet(tweet)
            
        return parsed_response

    def format_single_tweet(self, tweet: TweetModel) -> TweetModel:
        """
        Adjust the format of a single tweet.

        Args:
            tweet (TweetModel): The tweet to format

        Returns:
            TweetModel: The tweet formatted accordingly
        """
        prompt = tweet.text

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.crypto_market_analysis_format_tweet_system_prompt},
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
