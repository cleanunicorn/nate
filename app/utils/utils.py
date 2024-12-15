def clean_tweet(text):
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
    timeline = ""
    for tweet in tweets:
        timeline = (
            f"tweet_id: {tweet['id']} @{tweet['username']}: {tweet['text']}"
            + "\n---\n"
            + timeline
        )

    return timeline
