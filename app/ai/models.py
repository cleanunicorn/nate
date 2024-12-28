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


class CoinInfo(BaseModel):
    """Price information for a cryptocurrency."""
    current_price: float
    percent_change_24h: float
    volume_24h: float
    market_cap: float


class CryptoAnalysisThreadModel(TweetThreadModel):
    """Cryptocurrency analysis thread with market data and sentiment."""
    coins: List[CoinInfo]
    generated_at: str

