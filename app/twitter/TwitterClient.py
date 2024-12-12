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
            max_results=50,
            tweet_fields=["author_id", "in_reply_to_user_id", "conversation_id", "text"],
            expansions=["author_id"],
            user_fields=["username"],
        )

        homepage_tweets = []

        # Cache usernames
        # users = tweets[1]['users']
        # usernames = {}
        # for user in users:
        #     usernames[user['data']['id']] = {
        #         'name': usernames[user['data']['name']],
        #         'username': usernames[user['data']['username']]
        #     }

        for tweet in tweets.data:
            tweet_data = {}
            try:
                tweet_data["id"] = getattr(tweet, "id")
                tweet_data["text"] = getattr(tweet, "text")
                tweet_data["author_id"] = getattr(tweet, "author_id")
                tweet_data["conversation_id"] = getattr(tweet, "conversation_id")
                tweet_data["username"] = next(
                    user.username for user in tweets.includes["users"] if user.id == tweet.author_id
                )
            except:
                pass

            homepage_tweets.append(tweet_data)

        return homepage_tweets
