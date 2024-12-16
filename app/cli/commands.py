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
        bearer_token=getenv("TWITTER_BEARER_TOKEN"),
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
        bearer_token=getenv("TWITTER_BEARER_TOKEN"),
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


@twitter.command(name="reply")
@click.option(
    "--local",
    "-l",
    is_flag=True,
    help="Use locally stored tweets from database",
)
@click.option("--dry-run", "-d", is_flag=True, help="Generate tweet without posting")
def twitter_reply(local, dry_run):
    """Generate and post replies to conversations"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        bearer_token=getenv("TWITTER_BEARER_TOKEN"),
    )

    # Get conversations either from local DB or Twitter API
    conversations = client.get_conversations(use_local=local)

    # Filter for conversations needing replies
    pending_replies = {
        conv_id: conv
        for conv_id, conv in conversations.items()
        if client.needs_reply(conv)
    }

    if not pending_replies:
        click.echo("No conversations need replies")
        return

    generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"))

    # Display and process conversations needing replies
    click.echo(f"\nFound {len(pending_replies)} conversations needing replies:\n")

    for conv_id, conversation in pending_replies.items():
        click.echo(f"Conversation ID: {conv_id}")
        click.echo("Participants: " + ", ".join(conversation["participants"]))
        click.echo(f"Last activity: {conversation['last_tweet_time']}")
        click.echo("\nTweets:")

        # Sort tweets by creation time
        sorted_tweets = sorted(conversation["tweets"], key=lambda x: x["created_at"])

        for tweet in sorted_tweets:
            click.echo(f"\n@{tweet['username']} ({tweet['created_at']}):")
            click.echo(f"{tweet['text']}")

        conversation = sorted_tweets

        # Generate reply
        reply = generator.create_reply(timeline=conversation)

        # Adjust tone of tweet
        tone_agent = ToneAgent(api_key=getenv("OPENAI_API_KEY"))
        reply = tone_agent.adjust_tone_single_tweet(reply)        

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
                conversation_id=conv_id,
            )
            click.echo("Reply posted successfully!")
        else:
            click.echo("Dry run - reply not posted")


@twitter.command(name="handle-mentions")
@click.option("--dry-run", "-d", is_flag=True, help="Generate replies without posting")
@click.option(
    "--hours",
    "-h",
    default=24,
    help="Look for mentions from the last N hours (default: 24)",
)
def handle_mentions(dry_run, hours):
    """Generate and post replies to mentions of your account"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        bearer_token=getenv("TWITTER_BEARER_TOKEN"),
    )

    # Get mentions from Twitter API
    mentions = client.get_mentions(hours=hours)

    if not mentions:
        click.echo("No new mentions found")
        return

    generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"))

    click.echo(f"\nFound {len(mentions)} mentions to handle:\n")

    for mention in mentions:
        click.echo(f"Tweet from @{mention['username']} ({mention['created_at']}):")
        click.echo(f"Text: {mention['text']}")

        # Generate reply
        reply = generator.create_reply(timeline=[mention])

        # Adjust tone of reply
        tone_agent = ToneAgent(api_key=getenv("OPENAI_API_KEY"))
        reply = tone_agent.adjust_tone_single_tweet(reply)

        click.echo("\nGenerated Reply:")
        click.echo("---")
        click.echo(reply.text)
        click.echo("---")

        if not dry_run:
            client.post_reply(
                text=reply.text,
                reply_to_tweet_id=mention['id'],
                conversation_id=mention.get('conversation_id')
            )
            click.echo("Reply posted successfully!")
        else:
            click.echo("Dry run - reply not posted")
        
        click.echo("\n" + "-"*50 + "\n")

