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
            temperature=0.5,            # prompt requires very specific formatting rules, need consistent adherence to structure, still maintains enough creativity for the actual content (High temperature (1.2) could cause deviation from the required format)
            top_p=0.95,                 # we want high-quality outputs that match the exact format, helps maintain the structured requirements like number prefixes and icons, better for following the strict header information format
            frequency_penalty=0.1,      # we actually want some repetition in format elements, need consistent use of icons and numbering and still helps prevent content repetition
            presence_penalty=0.05       # format is very structured and repetitive by design, need consistent adherence to format rules and don't want the model to deviate from required elements
        )

        parsed_response = response.choices[0].message.parsed

        for i, tweet in enumerate(parsed_response.tweets):
            parsed_response.tweets[i] = self.format_single_tweet(tweet)
            
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
            temperature=0.7,        # provides a better balance between creativity and predictability, for formatting tasks, we want some consistency while maintaining engaging variations
            max_tokens=760, 
            top_p=0.9,              # allow for more high-quality options, works well with the lower temperature to maintain quality while allowing creativity
            frequency_penalty=0.3,  # encourage more diverse vocabulary usage, helps prevent repetitive phrases across tweets, particularly useful for crypto content where terms can get repetitive
            presence_penalty=0.1    # we want to stay focused on the topic, too high can force the model to deviate from important crypto terms, 0.1 still prevents excessive repetition while maintaining topic relevance
        )

        parsed_response = response.choices[0].message.parsed

        # Clean tweet
        parsed_response.text = clean_tweet(parsed_response.text)

        return parsed_response
