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


@twitter.command(name="reply")
@click.option(
    "--local",
    "-l",
    is_flag=True,
    help="Use locally stored tweets from database",
)
@click.option(
    "--dry-run", 
    "-d", 
    is_flag=True, 
    help="Generate tweet without posting"
)
@click.option(
    "--model",
    "-m",
    type=click.Choice(["openai", "ollama", "openrouter"]),
    default="openai",
    help="AI model to use for tweet generation",
)
def twitter_reply(local, dry_run, model):
    """Generate and post replies to conversations"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # Get bot's username
    bot_username = client.get_own_username()

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

    if model == "openai":
        generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"), bot_username=bot_username)
    elif model == "ollama":
        generator = TweetGeneratorOllama(bot_username=bot_username)
    else:
        click.echo("OpenRouter is currently disabled")
        return
    
    # Display and process conversations needing replies
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

        # Generate reply
        timeline = [{"username": t["username"], "text": t["text"]} for t in sorted_tweets]
        conversation_text = "\n".join([
            f"Tweet from @{t['username']}:\n{t['text']}" 
            for t in sorted_tweets
        ])
        
        reply = generator.create_reply(tweets=timeline, conversation=conversation_text)
        
        click.echo("\nGenerated Reply:")
        click.echo("---")
        click.echo(reply.text)
        click.echo("---")
        
        if not dry_run:
            # Get the last tweet in conversation to reply to
            last_tweet_id = sorted_tweets[-1]["id"]
            client.post_reply(
                text=reply.text,
                reply_to_tweet_id=last_tweet_id,
                conversation_id=conv_id
            )
            click.echo("Reply posted successfully!")
        else:
            click.echo("Dry run - reply not posted")
        
        click.echo("\n" + "-"*50 + "\n")