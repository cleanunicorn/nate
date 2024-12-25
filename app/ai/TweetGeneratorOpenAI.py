import logging

from openai import OpenAI

from app.ai.models import CryptoAnalysisThread, TweetModel, TweetThreadModel
from config.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TWITTER,
    TWITTER_PROMPT_SINGLE_TWEET,
    TWITTER_PROMPT_THREAD,
    TWITTER_PROMPT_REPLY,
    CRYPTO_SYSTEM_PROMPT,
    get_analysis_prompt
)
from app.utils.utils import format_tweet_timeline
from app.core.exceptions import AIGenerationError
from app.ai.agents.ToneAgent import ToneAgent

logger = logging.getLogger(__name__)


class TweetGeneratorOpenAI:
    def __init__(self, api_key: str):
        """
        Initialize the tweet generator with OpenAI API key
        
        Args:
            api_key (str): OpenAI API key for authentication
        """
        self.system = SYSTEM_PROMPT
        self.crypto_system = CRYPTO_SYSTEM_PROMPT
        self.prompt = USER_PROMPT_TWITTER
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4"

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
        category: str = 'latest',
        analysis_type: str = 'market_overview',
        tone_agent: ToneAgent = None
    ) -> CryptoAnalysisThread:
        """Create a cryptocurrency market analysis thread with optional tone adjustment.
        
        Args:
            market_data (dict): Market data from either search/trending or coins/markets endpoint
            category (str): Source of the data ('latest' for search trending, or 'visited'/'gainers'/'losers' for market data)
            analysis_type (str): Depth of analysis ('market_overview' or 'detailed_analysis')
            tone_agent (ToneAgent, optional): Agent for adjusting tweet tone
            
        Returns:
            CryptoAnalysisThread: Generated analysis thread with tweets and metadata
        """
        try:
            # Get the appropriate prompt based on category and analysis type
            prompt = get_analysis_prompt(
                category=category,
                analysis_type=analysis_type,
                market_data=market_data
            )
            
            # Generate initial analysis
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt}
                ],
                response_format=CryptoAnalysisThread,
                temperature=1.2,
                top_p=0.85,
                presence_penalty=0.15,
            )
            
            # Get the parsed content
            content = response.choices[0].message.parsed
            
            # Adjust tone if tone agent is provided
            if tone_agent:
                content = tone_agent.adjust_tone_thread(content)
            
            # Deduplicate mentions and return
            return self._deduplicate_mentions(content)
            
        except Exception as e:
            logger.error(f"Failed to generate crypto analysis: {str(e)}")
            raise AIGenerationError("Failed to generate cryptocurrency analysis") from e