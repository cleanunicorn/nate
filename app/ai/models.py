from typing import Optional
from pydantic import BaseModel
from dataclasses import dataclass
from typing import List


class TweetModel(BaseModel):
    quote_tweet_id: Optional[int]
    text: str
    username: str


class TweetThreadModel(BaseModel):
    tweets: list[TweetModel]
    topic: str


class CryptoTweetModel(BaseModel):
    text: str
    quote_tweet_id: Optional[str] = None


class CryptoAnalysisThread(BaseModel):
    topic: str
    market_summary: str
    tweets: List[CryptoTweetModel]

    class Config:
        schema_extra = {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "market_summary": {"type": "string"},
                "tweets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "quote_tweet_id": {"type": ["string", "null"]}
                        },
                        "required": ["text"]
                    }
                }
            },
            "required": ["topic", "market_summary", "tweets"]
        }
