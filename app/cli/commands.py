"""CLI commands for the Nate social media assistant application."""

from os import getenv

import click
from dotenv import load_dotenv
from app.twitter.TwitterClient import TwitterClient
from app.ai.TweetGeneratorOpenAI import TweetGeneratorOpenAI
from app.ai.TweetGeneratorOllama import TweetGeneratorOllama

# from app.ai.TweetGeneratorOpenRouter import TweetGeneratorOpenRouter
from app.ai.agents.ToneAgent import ToneAgent
from app.utils.utils import clean_tweet

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

        # Adjust tone of tweet thread
        tone_agent = ToneAgent(api_key=getenv("OPENAI_API_KEY"))
        new_tweet_thread = tone_agent.adjust_tone_thread(new_tweet_thread.tweets)

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

        # Adjust tone of tweet
        tone_agent = ToneAgent(api_key=getenv("OPENAI_API_KEY"))
        new_post = tone_agent.adjust_tone_single_tweet(new_post.text)

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
