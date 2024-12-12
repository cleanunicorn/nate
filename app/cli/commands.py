"""CLI commands for the Nate social media assistant application."""

from os import getenv

import click
from dotenv import load_dotenv
from app.twitter.TwitterClient import TwitterClient
from app.ai.TweetGeneratorOpenAI import TweetGeneratorOpenAI
from app.ai.TweetGeneratorOllama import TweetGeneratorOllama
from app.ai.TweetGeneratorOpenRouter import TweetGeneratorOpenRouter
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
def twitter_post(model, dry_run, thread):
    """Generate and post a tweet or thread based on timeline analysis"""
    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # Get timeline and simplify
    # timeline = client.get_timeline()
    # simplified_timeline = [
    #     {"username": t["username"], "text": t["text"]} for t in timeline
    # ]
    simplified_timeline = [
        {"username": "Darrenlautf", "text": "Huge\ud83d\udc40 https://t.co/sdAx1SkiUN"},
        {
            "username": "VoldiemortEth",
            "text": "RT @batzdu: you: calling tops, liquidated, panicking \n\nme: https://t.co/fWSoMPyY1v",
        },
        {
            "username": "aixbt_agent",
            "text": "bridged to solana via twitter language processing. first of its kind. revenue split 50/50 between deployers and $emp treasury",
        },
        {
            "username": "aixbt_agent",
            "text": "innovative liquidity bands on uniswap v3 make launches sniper-proof. market noticed - 3m to 30m mcap in hours\n\n4.3m daily volume",
        },
        {
            "username": "aixbt_agent",
            "text": "$simmi first to enable token launches through twitter commands. agent to agent interaction driving real revenue. 500k in fees ready for deployment",
        },
        {"username": "evan_van_ness", "text": "RT @SrMiguelV: 2017 nunca muri\u00f3."},
        {
            "username": "Darrenlautf",
            "text": "RT @BeamFDN: \ud83c\udf08Beam\u2019s biggest announcement ever is finally here.\n\n\u25b6\ufe0fWatch the video below.\n\nFour projects shaping our future:\n\n1. Global Exp\u2026",
        },
        {
            "username": "evan_van_ness",
            "text": "Should we fund a Third Foundation for Ethereum?",
        },
        {
            "username": "RoundtableSpace",
            "text": "PARTNERSHIP: Guess what\u2019s cuter than unicorns and it actually exists. \n\nMeet @AstroArmadillos, a multiplayer web and mobile free-to-play party game, which blends the fast-paced action of games like Stumble Guys and Brawl Stars.\n\nAstro Armadillos is redefining Web3 education by\u2026 https://t.co/MIiqgz7r2A https://t.co/zatOy2NRap",
        },
        {
            "username": "libevm",
            "text": "\u201cS/o - Rust\u201d - @gakonst \n\nat @ethmelbourne dec meetup https://t.co/0f1w4abAvL",
        },
        {"username": "nullinger", "text": "GM, flashcrash survivooors."},
    ]

    # Select generator based on model option
    if model == "openai":
        generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"))
    elif model == "ollama":
        generator = TweetGeneratorOllama()
    else:
        generator = TweetGeneratorOpenRouter()

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
