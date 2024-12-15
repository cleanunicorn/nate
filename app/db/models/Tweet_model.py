from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.db.Init_db import Base

class Tweet(Base):
    __tablename__ = 'tweets'
    
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String, unique=True)
    text = Column(String)
    author_id = Column(String)
    conversation_id = Column(String)
    username = Column(String)
    in_reply_to_user_id = Column(String, nullable=True)
    fetched_for_user = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))