from openai import OpenAI

from app.ai.models import CryptoAnalysisThread, TweetModel, TweetThreadModel
from config.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TWITTER,
    TWITTER_PROMPT_SINGLE_TWEET,
    TWITTER_PROMPT_THREAD,
    TWITTER_PROMPT_REPLY,
    CRYPTO_SYSTEM_PROMPT,
    CRYPTO_ANALYSIS_PROMPT,
    CRYPTO_MARKET_OVERVIEW_PROMPT,
)
from app.utils.utils import format_tweet_timeline


class TweetGeneratorOpenAI:
    def __init__(self, api_key: str):
        self.system = SYSTEM_PROMPT
        self.crypto_system = CRYPTO_SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER
        self.client = OpenAI(api_key=api_key)

    def _deduplicate_mentions(self, content: TweetModel | TweetThreadModel) -> TweetModel | TweetThreadModel:
        mentioned_tweets = {}
        # Return single tweets without changes
        if isinstance(content, TweetModel):
            return content

        # Initialize empty dict for tracking mentioned tweets
        # Allow a tweet to be mentioned only once
        for tweet in content.tweets:
            # If the tweet is mentioned, remove the quote_tweet_id
            if mentioned_tweets.get(tweet.quote_tweet_id, False):
                tweet.quote_tweet_id = None
            else:
                mentioned_tweets[tweet.quote_tweet_id] = True
        return content

    def create_tweet(
        self,
        timeline: list[dict],
        response_format: any = TweetModel,
        action: str = TWITTER_PROMPT_SINGLE_TWEET,
    ) -> TweetModel | TweetThreadModel:
        messages = [
            {"role": "system", "content": self.system},
            {
                "role": "user",
                "content": self.prompt.format(
                    twitter_timeline=format_tweet_timeline(timeline),
                    twitter_action=action,
                ),
            },
        ]

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=response_format,
            temperature=1.2,
            top_p=0.85,
            # frequency_penalty=0.2,
            presence_penalty=0.15,
        )

        content = response.choices[0].message.parsed

        # Clean up mentions
        content = self._deduplicate_mentions(content)

        return content

    def create_thread(self, timeline: list[dict]) -> TweetThreadModel:
        return self.create_tweet(
            timeline=timeline,
            action=TWITTER_PROMPT_THREAD,
            response_format=TweetThreadModel,
        )

    def create_reply(self, timeline: list[dict]) -> TweetModel:
        return self.create_tweet(
            timeline=timeline,
            action=TWITTER_PROMPT_REPLY,
            response_format=TweetModel,
        )

    def _format_crypto_data(self, data: dict) -> str:
        """Format crypto market data for the prompt"""
        formatted_data = []
        for asset in data.get("assets", []):
            formatted_data.append(
                f"Asset: {asset['symbol']}\n"
                f"Price: ${asset['price']:,.2f}\n"
                f"24h Change: {asset['change_24h']}%\n"
                f"Volume: ${asset['volume']:,.0f}\n"
            )
        return "\n".join(formatted_data)

    def create_crypto_analysis(
        self,
        market_data: dict,
        analysis_type: str = "general",
        response_format: type = CryptoAnalysisThread,
    ) -> CryptoAnalysisThread:
        """Generate crypto market analysis tweets"""
        formatted_data = self._format_crypto_data(market_data)
        
        prompt = (
            CRYPTO_MARKET_OVERVIEW_PROMPT
            if analysis_type == "market_overview"
            else CRYPTO_ANALYSIS_PROMPT
        )

        messages = [
            {"role": "system", "content": self.crypto_system},
            {
                "role": "user",
                "content": prompt.format(market_data=formatted_data),
            },
        ]

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=response_format,
            temperature=1.2,
            top_p=0.85,
            presence_penalty=0.15,
        )

        content = response.choices[0].message.parsed
        return self._deduplicate_mentions(content)
