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

def is_likely_spam(tweet_data):
    """
    Check if a tweet is likely spam based on various indicators
    
    Args:
        tweet_data (dict): Tweet data containing at least 'text' and 'username' fields
        
    Returns:
        bool: True if tweet is likely spam, False otherwise
    """
    spam_indicators = 0
    text = tweet_data['text'].lower()
    
    t_co_count = text.count("https://t.co/")
    if t_co_count > 0:
        spam_indicators += min(t_co_count * 1, 2)
        
    # Check for multiple @ mentions (more than 3)
    tag_count = text.count("@")
    if tag_count > 2:
        spam_indicators += min(tag_count * 0.5, 2)
        
    # Check for common spam phrases
    spam_phrases = ["airdrop", "biggest", "lfg", "token distribution", "claim", "giveaway"]
    for phrase in spam_phrases:
        if phrase in text:
            spam_indicators += 1
            
    # Check for numeric usernames
    if any(c.isdigit() for c in tweet_data['username']):
        spam_indicators += 0.5
        
    # Consider it spam if it has multiple spam indicators
    return spam_indicators >= 3
