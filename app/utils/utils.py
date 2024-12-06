def clean_tweet(text):
    # Remove surrounding triple backticks if present
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()

    # Remove surrounding double quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()

    return text
