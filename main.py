from os import getenv
from dotenv import load_dotenv
import json
from app.twitter.TwitterClient import TwitterClient

# from app.ai.TweetGeneratorOllama import TweetGeneratorOllama
from app.ai.TweetGeneratorOpenRouter import TweetGeneratorOpenRouter
from app.utils.utils import clean_tweet

# Load auth keys
load_dotenv()

client = TwitterClient(
    api_key=getenv("TWITTER_API_KEY"),
    api_secret=getenv("TWITTER_API_SECRET"),
    access_token=getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
)

timeline = client.get_timeline()

print(timeline)

# simplified_timeline = []
# for t in timeline:
#     simplified_timeline.append({"author": "", "text": t["text"]})

# generator = TweetGeneratorOpenRouter(api_key=getenv("OPENROUTER_API_KEY"))

# new_tweet = generator.create_tweet(tweets=json.dumps(simplified_timeline))

# new_tweet = clean_tweet(new_tweet)

# client.post_tweet(new_tweet)

# print(new_tweet)
