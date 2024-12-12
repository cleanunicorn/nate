from pydantic import BaseModel

class TweetThreadFormat(BaseModel):
    tweets: list[str]
    topic: str

class TweetFormat(BaseModel):
    text: str
    topic: str 