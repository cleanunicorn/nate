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
        timeline = f"@{tweet['username']}: {tweet['text']}\n---\n" + timeline

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
    
    # Check for suspicious URLs
    if "https://t.co/" in text:
        spam_indicators += 1
        
    # Check for multiple @ mentions (more than 3)
    if text.count("@") > 2:
        spam_indicators += 1
        
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
