def clean_tweet(text):
    """
    Clean tweet text by removing backticks, quotes, and hashtags.

    Args:
        text (str): The tweet text to clean

    Returns:
        str: The cleaned tweet text
    """
    # Remove surrounding triple backticks if present
    text = text.strip()
    text = text.strip("```")
    text = text.strip()
    text = text.strip('"')
    text = text.strip()

    # Remove hashtags
    text = " ".join(word for word in text.split() if not word.startswith("#"))

    return text


def format_tweet_timeline(tweets) -> str:
    """
    Format a list of tweets into a timeline string.

    Args:
        tweets (list): List of tweet dictionaries containing id, username, and text

    Returns:
        str: Formatted timeline string
    """
    timeline = ""
    for tweet in tweets:
        timeline = (
            f"tweet_id:{tweet['id']}\n"
            + "@{tweet['username']}:{tweet['text']}\n"
            + "---\n"
            + timeline
        )

    return timeline
