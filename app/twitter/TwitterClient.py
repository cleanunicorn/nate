import tweepy
from app.db.Init_db import init_db
from app.db.models.Tweet_model import Tweet
from datetime import datetime, timezone

class TwitterClient:
    def __init__(self, api_key, api_secret, access_token, access_token_secret, db_path='tweets.db'):
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )
        # Initialize database connection
        self.engine, Session = init_db(db_path)
        self.Session = Session


    def save_tweet_to_db(self, tweet_data, fetched_for_user=None):
        """Save tweet to database with user context"""
        session = self.Session()
        try:
            # First try to find existing tweet
            existing_tweet = session.query(Tweet).filter_by(tweet_id=str(tweet_data["id"])).first()
            
            if existing_tweet:
                # Update existing tweet if needed
                existing_tweet.fetched_for_user = fetched_for_user
                existing_tweet.created_at = datetime.now(timezone.utc)
            else:
                # Create new tweet if it doesn't exist
                tweet = Tweet(
                    tweet_id=str(tweet_data["id"]),
                    text=tweet_data["text"],
                    author_id=tweet_data["author_id"],
                    conversation_id=tweet_data["conversation_id"],
                    username=tweet_data["username"],
                    fetched_for_user=fetched_for_user,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(tweet)
                
            session.commit()
        except Exception as e:
            print(f"Error saving tweet to database: {e}")
            session.rollback()
        finally:
            session.close()
    
    def post_tweet(self, text):
        self.client.create_tweet(text=text)

    def get_cached_tweets(self, limit=50):
        """Retrieve tweets from the local database"""
        session = self.Session()
        try:
            tweets = session.query(Tweet).order_by(Tweet.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": tweet.tweet_id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "conversation_id": tweet.conversation_id,
                    "username": tweet.username,
                    "cached_at": tweet.created_at
                }
                for tweet in tweets
            ]
        finally:
            session.close()

    def get_timeline(self, user_id=None, use_cache=True, update_cache=True):
        """
        Get timeline tweets with flexible caching options
        
        Args:
            user_id (str): The user ID to fetch timeline for. If None, gets authenticated user's timeline
            use_cache (bool): If True, returns cached tweets
            update_cache (bool): If True, fetches new tweets and updates cache
        """
        timeline_tweets = []
        
        # Get cached tweets if requested
        if use_cache:
            session = self.Session()
            try:
                query = session.query(Tweet).order_by(Tweet.created_at.desc())
                if user_id:
                    query = query.filter(Tweet.author_id == user_id)
                tweets = query.limit(50).all()
                timeline_tweets.extend([
                    {
                        "id": tweet.tweet_id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "conversation_id": tweet.conversation_id,
                        "username": tweet.username,
                        "in_reply_to_user_id": tweet.in_reply_to_user_id,
                        "cached_at": tweet.created_at
                    }
                    for tweet in tweets
                ])
            finally:
                session.close()
                
        # Fetch and cache new tweets if requested
        if update_cache:
            try:
                if user_id:
                    tweets = self.client.get_users_tweets(
                        id=user_id,
                        max_results=50,
                        tweet_fields=["author_id", "in_reply_to_user_id", "conversation_id"],
                        expansions=["author_id", "in_reply_to_user_id"],
                        user_fields=["username"],
                        user_auth=True
                    )
                else:
                    tweets = self.client.get_home_timeline(
                        max_results=50,
                        tweet_fields=["author_id", "in_reply_to_user_id", "conversation_id"],
                        expansions=["author_id", "in_reply_to_user_id"],
                        user_fields=["username"],
                    )

                if tweets and tweets.data:
                    for tweet in tweets.data:
                        tweet_data = {}
                        try:
                            tweet_data["id"] = getattr(tweet, "id")
                            tweet_data["text"] = getattr(tweet, "text")
                            tweet_data["author_id"] = getattr(tweet, "author_id")
                            tweet_data["conversation_id"] = getattr(tweet, "conversation_id")
                            tweet_data["in_reply_to_user_id"] = getattr(tweet, "in_reply_to_user_id", None)

                            tweet_data["username"] = next(
                                user.username for user in tweets.includes["users"] if user.id == tweet.author_id
                            )
                            
                            # Save to database with user context
                            self.save_tweet_to_db(tweet_data, user_id)
                            
                            # Only add to return list if we're not using cache
                            if not use_cache:
                                timeline_tweets.append(tweet_data)
                                
                        except Exception as e:
                            print(f"Error processing tweet: {e}")
                            continue
                        
            except Exception as e:
                print(f"Error fetching timeline: {e}")

        return timeline_tweets
    

    def get_user_id(self, username):
        """Get user ID from username"""
        try:
            # Use user lookup endpoint
            user = self.client.get_user(username=username, user_auth=True)
            if user.data:
                return user.data.id
            return None
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return None

    def get_username(self, user_id):
        """Get username from user ID"""
        try:
            # Use user lookup endpoint with ID
            user = self.client.get_user(id=user_id, user_auth=True)
            if user.data:
                return user.data.username
            return None
        except Exception as e:
            print(f"Error getting username: {e}")
            return None