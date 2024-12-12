import click
from os import getenv
from dotenv import load_dotenv
from app.twitter.TwitterClient import TwitterClient
from app.ai.TweetGeneratorOpenAI import TweetGeneratorOpenAI
from app.ai.TweetGeneratorOllama import TweetGeneratorOllama
from app.ai.TweetGeneratorOpenRouter import TweetGeneratorOpenRouter
from app.utils.utils import clean_tweet

@click.group()
def cli():
    """Nate - Your AI-powered social media assistant"""
    pass

@cli.group()
def twitter():
    """Twitter-related commands"""
    pass

@twitter.command(name='post')
@click.option('--model', '-m',
              type=click.Choice(['openai', 'ollama', 'openrouter']),
              default='openai',
              help='AI model to use for tweet generation')
@click.option('--dry-run', '-d',
              is_flag=True,
              help='Generate tweet without posting')
def twitter_post(model, dry_run):
    """Generate and post a tweet based on timeline analysis"""
    # Load auth keys
    load_dotenv()

    # Initialize Twitter client
    client = TwitterClient(
        api_key=getenv("TWITTER_API_KEY"),
        api_secret=getenv("TWITTER_API_SECRET"),
        access_token=getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )

    # Get timeline and simplify
    timeline = client.get_timeline()
    simplified_timeline = [
        {"username": t["username"], "text": t["text"]}
        for t in timeline
    ]

    # Select generator based on model option
    if model == 'openai':
        generator = TweetGeneratorOpenAI(api_key=getenv("OPENAI_API_KEY"))
    elif model == 'ollama':
        generator = TweetGeneratorOllama()
    else:
        generator = TweetGeneratorOpenRouter()

    # Generate new tweet
    new_tweet = generator.create_tweet(tweets=simplified_timeline)
    new_tweet = clean_tweet(new_tweet)

    click.echo("Generated Tweet:")
    click.echo("---")
    click.echo(new_tweet)
    click.echo("---")

    if not dry_run:
        client.post_tweet(new_tweet)
        click.echo("Tweet posted successfully!")
    else:
        click.echo("Dry run - tweet not posted")