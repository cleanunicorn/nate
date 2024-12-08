import tweepy


class TwitterClient:
    def __init__(self, api_key, api_secret, access_token, access_token_secret):
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True,
        )

    def post_tweet(self, text):
        self.client.create_tweet(text=text)

    def get_timeline(self):
        tweets = self.client.get_home_timeline(
            max_results=2,
            tweet_fields=["author_id", "username", "in_reply_to_user_id", "conversation_id"],
            user_fields=["name"],
            expansions=["author_id"],
        )

        homepage_tweets = []

        users = {user.id: user for user in tweets.includes['users']} if 'users' in tweets.includes else {}

        for tweet in tweets.data:
            tweet_data = {}
            try:
                tweet_data["id"] = getattr(tweet, "id")
                tweet_data["text"] = getattr(tweet, "text")
                tweet_data["author_id"] = getattr(tweet, "author_id")
                tweet_data["conversation_id"] = getattr(tweet, "conversation_id")
                tweet_data["username"] = users[tweet.author_id].username if tweet.author_id in users else None
            except Exception as e:
                print(e)

            homepage_tweets.append(tweet_data)

        return homepage_tweets

    def get_mentions(self):
        mentions = self.client.get_users_mentions(
            id=self.client.get_me().data.id,
            max_results=5,
            tweet_fields=["author_id", "conversation_id", "created_at"],
            user_fields=["name"],
            expansions=["author_id"]
        )

        mention_tweets = []

        users = {user.id: user for user in mentions.includes['users']} if 'users' in mentions.includes else {}

        for tweet in mentions.data or []:
            tweet_data = {}
            try:
                tweet_data["id"] = getattr(tweet, "id")
                tweet_data["text"] = getattr(tweet, "text")
                tweet_data["author_id"] = getattr(tweet, "author_id")
                tweet_data["conversation_id"] = getattr(tweet, "conversation_id")
                tweet_data["created_at"] = getattr(tweet, "created_at")
                tweet_data["username"] = users[tweet.author_id].username if tweet.author_id in users else None
            except Exception as e:
                print(e)

            mention_tweets.append(tweet_data)

        return mention_tweets
