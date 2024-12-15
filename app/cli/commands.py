"""CLI commands for the Nate social media assistant application."""

from os import getenv

import click
from dotenv import load_dotenv
from app.twitter.TwitterClient import TwitterClient
from app.ai.TweetGeneratorOpenAI import TweetGeneratorOpenAI
from app.ai.TweetGeneratorOllama import TweetGeneratorOllama
from app.ai.TweetGeneratorOpenRouter import TweetGeneratorOpenRouter
from app.utils.utils import clean_tweet
from app.db.models.Tweet_model import Tweet

# Load environment variables at module level
load_dotenv()


@click.group()
def cli():
    """Nate - Your AI-powered social media assistant"""
    pass


@cli.group()
def twitter():
    """Twitter-related commands"""
    pass


@twitter.command(name="post")
@click.option(
    "--model",
    "-m",
    type=click.Choice(["openai", "ollama", "openrouter"]),
    default="openai",
    help="AI model to use for tweet generation",
)
@click.option("--dry-run", "-d", is_flag=True, help="Generate tweet without posting")
@click.option(
    "--thread",
    "-t",
    is_flag=True,
    help="Generate a thread of tweets instead of a single tweet",
)
@click.option(
    "--sample",
    "-s",
    is_flag=True,
    help="Use sample data instead of real Twitter timeline",
)
def twitter_post(model, dry_run, thread, sample):
    """Generate and post a tweet or thread based on timeline analysis"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # Get timeline and simplify
    if sample:
        timeline = client.get_sample_timeline()
    else:
        timeline = client.get_timeline()

    simplified_timeline = [
        {"username": t["username"], "text": t["text"]} for t in timeline
    ]

    # Select generator based on model option
    if model == "openai":
        generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"))
    elif model == "ollama":
        generator = TweetGeneratorOllama()
    else:
        click.echo("OpenRouter is currently disabled")
        return
        # generator = TweetGeneratorOpenRouter(api_key=getenv("OPENROUTER_API_KEY"))

    # Generate new tweet or thread
    if thread:
        new_tweet_thread = generator.create_thread(tweets=simplified_timeline)

        new_topic = new_tweet_thread.topic
        new_tweets = new_tweet_thread.tweets

        # Clean tweets and filter out empty ones
        new_tweets = [clean_tweet(tweet) for tweet in new_tweets]
        new_tweets = [tweet for tweet in new_tweets if len(tweet) > 0]

        click.echo("Generated Thread:")
        click.echo(f"Topic: {new_topic}")
        click.echo("---")
        for i, tweet in enumerate(new_tweets, 1):
            click.echo(f"Tweet {i}:")
            click.echo(tweet)
            click.echo("---")

        if not dry_run and thread:  # Only post if there are valid tweets
            client.post_thread(new_tweets)
            click.echo("Thread posted successfully!")
        elif not thread:
            click.echo("No valid tweets generated")
        else:
            click.echo("Dry run - thread not posted")
    else:
        new_post = generator.create_tweet(tweets=simplified_timeline)

        new_topic = new_post.topic
        new_tweet = clean_tweet(new_post.text)

        click.echo("Generated Tweet:")
        click.echo(f"Topic: {new_topic}")
        click.echo("---")
        click.echo(new_tweet)
        click.echo("---")

        if not dry_run:
            client.post_tweet(new_tweet)
            click.echo("Tweet posted successfully!")
        else:
            click.echo("Dry run - tweet not posted")


@twitter.command(name="replies")
@click.option(
    "--local",
    "-l",
    is_flag=True,
    help="Use locally stored tweets from database",
)

def twitter_replies(local):
    """List conversations that need replies"""
    click.echo(f"is local: {local}")
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # Get conversations either from local DB or Twitter API
    conversations = client.get_conversations(use_local=local)

    # Filter for conversations needing replies
    pending_replies = {
        conv_id: conv for conv_id, conv in conversations.items() 
        if client.needs_reply(conv)
    }

    if not pending_replies:
        click.echo("No conversations need replies")
        return

    # Display conversations needing replies
    click.echo(f"\nFound {len(pending_replies)} conversations needing replies:\n")
    
    for conv_id, conversation in pending_replies.items():
        click.echo(f"Conversation ID: {conv_id}")
        click.echo("Participants: " + ", ".join(conversation["participants"]))
        click.echo(f"Last activity: {conversation['last_tweet_time']}")
        click.echo("\nTweets:")
        
        # Sort tweets by creation time
        sorted_tweets = sorted(
            conversation["tweets"], 
            key=lambda x: x["created_at"]
        )
        
        for tweet in sorted_tweets:
            click.echo(f"\n@{tweet['username']} ({tweet['created_at']}):")
            click.echo(f"{tweet['text']}")
        
        click.echo("\n" + "-"*50 + "\n")
    """List conversations that need replies"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    if local:
        # Get tweets from local database
        session = client.Session()
        try:
            stored_tweets = session.query(Tweet).all()
            
            # Convert stored tweets to the format expected by _process_tweets_into_conversations
            tweets_data = []
            for tweet in stored_tweets:
                tweets_data.append({
                    "id": tweet.tweet_id,
                    "text": tweet.text,
                    "author_id": tweet.author_id,
                    "username": tweet.username,
                    "conversation_id": tweet.conversation_id,
                    "created_at": tweet.created_at,
                })
            
            # Process tweets into conversations
            conversations = {}
            for tweet in tweets_data:
                conv_id = tweet["conversation_id"]
                if conv_id not in conversations:
                    conversations[conv_id] = {
                        "tweets": [],
                        "participants": set(),
                        "last_tweet_time": None,
                        "our_last_tweet_time": None
                    }
                
                conversations[conv_id]["tweets"].append(tweet)
                conversations[conv_id]["participants"].add(tweet["username"])
                
                # Track latest tweet time
                tweet_time = tweet["created_at"]
                if (conversations[conv_id]["last_tweet_time"] is None or 
                    tweet_time > conversations[conv_id]["last_tweet_time"]):
                    conversations[conv_id]["last_tweet_time"] = tweet_time
                
                # Track our last tweet time if we're the author
                if tweet["username"] == client.get_own_username():
                    if (conversations[conv_id]["our_last_tweet_time"] is None or
                        tweet_time > conversations[conv_id]["our_last_tweet_time"]):
                        conversations[conv_id]["our_last_tweet_time"] = tweet_time
            
            # Get pending replies from processed conversations
            pending_replies = {
                conv_id: conv for conv_id, conv in conversations.items() 
                if client.needs_reply(conv)
            }
            
        finally:
            session.close()
    else:
        # Get pending replies from Twitter API
        pending_replies = client.get_pending_replies()

    if not pending_replies:
        click.echo("No conversations need replies")
        return

    # Display conversations needing replies
    click.echo(f"\nFound {len(pending_replies)} conversations needing replies:\n")
    
    for conv_id, conversation in pending_replies.items():
        click.echo(f"Conversation ID: {conv_id}")
        click.echo("Participants: " + ", ".join(conversation["participants"]))
        click.echo(f"Last activity: {conversation['last_tweet_time']}")
        click.echo("\nTweets:")
        
        # Sort tweets by creation time
        sorted_tweets = sorted(
            conversation["tweets"], 
            key=lambda x: x["created_at"]
        )
        
        for tweet in sorted_tweets:
            click.echo(f"\n@{tweet['username']} ({tweet['created_at']}):")
            click.echo(f"{tweet['text']}")
        
        click.echo("\n" + "-"*50 + "\n")
    """List conversations that need replies"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # Get pending replies
    pending_replies = client.get_pending_replies()

    if not pending_replies:
        click.echo("No conversations need replies")
        return

    # Display conversations needing replies
    click.echo(f"\nFound {len(pending_replies)} conversations needing replies:\n")
    
    for conv_id, conversation in pending_replies.items():
        click.echo(f"Conversation ID: {conv_id}")
        click.echo("Participants: " + ", ".join(conversation["participants"]))
        click.echo(f"Last activity: {conversation['last_tweet_time']}")
        click.echo("\nTweets:")
        
        # Sort tweets by creation time
        sorted_tweets = sorted(
            conversation["tweets"], 
            key=lambda x: x["created_at"]
        )
        
        for tweet in sorted_tweets:
            click.echo(f"\n@{tweet['username']} ({tweet['created_at']}):")
            click.echo(f"{tweet['text']}")
        
        click.echo("\n" + "-"*50 + "\n")