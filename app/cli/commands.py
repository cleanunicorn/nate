"""CLI commands for the Nate social media assistant application."""

from os import getenv
from pathlib import Path

import click
from dotenv import load_dotenv

# Group app imports together
from app.ai.agents.ToneAgent import ToneAgent
from app.ai.TweetGeneratorOpenAI import TweetGeneratorOpenAI
from app.twitter.TwitterClient import TwitterClient

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
def twitter_post(dry_run, thread, sample):
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

    # Initialize tweet generator
    generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"))
    # Generate new tweet or thread
    if thread:
        new_tweet_thread = generator.create_thread(timeline=timeline)

        # Adjust tone of tweet thread
        tone_agent = ToneAgent(api_key=getenv("OPENAI_API_KEY"))
        new_tweet_thread = tone_agent.adjust_tone_thread(new_tweet_thread)

        click.echo("Generated Thread:")
        click.echo(f"Topic: {new_tweet_thread.topic}")
        click.echo("---")
        for i, tweet in enumerate(new_tweet_thread.tweets, 1):
            click.echo(f"Tweet {i}:")
            click.echo(f"Quote Tweet ID: {tweet.quote_tweet_id}")
            click.echo(tweet.text)
            click.echo("---")

        if not dry_run and thread:  # Only post if there are valid tweets
            client.post_thread(new_tweet_thread)
            click.echo("Thread posted successfully!")
        elif not thread:
            click.echo("No valid tweets generated")
        else:
            click.echo("Dry run - thread not posted")
    else:
        new_post = generator.create_tweet(timeline=timeline)

        # Adjust tone of tweet
        tone_agent = ToneAgent(api_key=getenv("OPENAI_API_KEY"))
        new_post = tone_agent.adjust_tone_single_tweet(new_post)

        click.echo("Generated Tweet")
        click.echo(f"Quote Tweet ID: {new_post.quote_tweet_id}")
        click.echo("---")
        click.echo(new_post.text)
        click.echo("---")

        if not dry_run:
            client.post_tweet(new_post)
            click.echo("Tweet posted successfully!")
        else:
            click.echo("Dry run - tweet not posted")


@twitter.command(name="follow")
@click.option("--users", "-u", help="Comma-separated list of usernames to follow")
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True),
    help="File containing usernames (one per line)",
)
def follow_users(users, file):
    """Follow multiple users specified directly or from a file."""
    if not users and not file:
        click.echo("Error: Please provide either --users or --file option")
        return

    usernames = set()

    if users:
        # Add usernames from command line
        usernames.update(username.strip() for username in users.split(","))

    if file:
        # Add usernames from file
        file_path = Path(file)
        try:
            with file_path.open("r", encoding="utf-8") as f:
                file_usernames = [line.strip() for line in f if line.strip()]
                usernames.update(file_usernames)
        except Exception as e:
            click.echo(f"Error reading file: {e}")
            return

    if not usernames:
        click.echo("No valid usernames provided")
        return

    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    success_count = 0
    for username in usernames:
        try:
            # Remove '@' if present
            if username.startswith("@"):
                username = username[1:]

            # Assuming there's an existing follow_user function in the API client
            if client.follow_user(username):
                click.echo(f"Successfully followed @{username}")
                success_count += 1
            else:
                click.echo(f"Failed to follow @{username}")
        except Exception as e:
            click.echo(f"Failed to follow @{username}: {e}")

    click.echo(f"\nFollowed {success_count} out of {len(usernames)} users")
