from typing import Optional
from pydantic import BaseModel


class TweetModel(BaseModel):
    quote_tweet_id: Optional[int]
    text: str
    username: str


class TweetThreadModel(BaseModel):
    tweets: list[TweetModel]
    topic: str
