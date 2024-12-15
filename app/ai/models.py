from typing import Optional
from pydantic import BaseModel


class Tweet(BaseModel):
    quote_tweet_id: Optional[int]
    text: str
    username: str


class TweetThreadModel(BaseModel):
    tweets: list[Tweet]
    topic: str


class TweetModel(BaseModel):
    tweet: Tweet
    topic: str
