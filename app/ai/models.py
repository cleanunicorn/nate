from typing import List, Optional, Literal
from datetime import datetime, timezone
from pydantic import BaseModel


class TweetModel(BaseModel):
    """Single tweet with metadata."""
    quote_tweet_id: Optional[str]
    text: str
    username: str


class TweetThreadModel(BaseModel):
    """Base class for tweet threads."""
    topic: str
    tweets: List[TweetModel]
    timestamp: str


class CoinPrice(BaseModel):
    """Price information for a cryptocurrency."""
    current_price: float
    percent_change_24h: float
    volume_24h: float
    market_cap: float


class TrendingCoin(BaseModel):
    """Standardized coin data model."""
    id: str
    symbol: str
    name: str
    price_data: CoinPrice
    rank: Optional[int] = None
    last_updated: str


class MarketSentiment(BaseModel):
    """Overall market sentiment analysis."""
    trend: Literal['bullish', 'bearish', 'neutral']
    strength: Literal['strong', 'moderate', 'weak']
    volume_rating: Literal['high', 'moderate', 'low']
    key_factors: List[str]
    timestamp: str


class CryptoAnalysisThreadModel(TweetThreadModel):
    """Cryptocurrency analysis thread with market data and sentiment."""
    coins: List[CoinPrice]
    generated_at: str

