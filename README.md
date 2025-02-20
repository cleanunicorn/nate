# AI Tweet Generator Bot

A versatile Twitter bot that generates and posts tweets using multiple AI language models including OpenAI, Ollama, and OpenRouter.

## Features

- Generate tweets using different AI models:
  - OpenAI GPT models
  - Ollama local models
  - OpenRouter API
- Automated tweet posting
- Command-line interface for easy management
- Configurable prompt templates
- Utility functions for text processing
- Cryptocurrency market analysis thread tweets
  - Trending coins analysis
  - Market gainers/losers/visited/latest tracking
  - Detailed market insights or shorter market overview


## Prerequisites

- Python 3.8+
- Twitter Developer Account with API credentials
- Access to one or more of the supported AI platforms:
  - OpenAI API key
  - Ollama installation
  - OpenRouter API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-tweet-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with the following variables:
```env
# Twitter API Credentials
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# AI Platform credentials (add the ones you plan to use)
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Cryptocurrency API Credentials
COINGECKO_API_KEY=your_coingecko_api_key
```

## Usage

### Running with Docker

```bash
docker build -t ai-tweet-generator .
docker run -d ai-tweet-generator
```

### Running Locally

Use the provided shell script:
```bash
./run.sh
```

Or run directly with Python:
```bash
python main.py
```

### Command-line Interface

The bot comes with several CLI commands for management:

```bash
# Generate and post a tweet
python main.py twitter post

# Generate a tweet without posting
python main.py twitter post --dry-run

# Generate cryptocurrency market analysis
python main.py twitter trending-crypto --category gainers
python main.py twitter trending-crypto --category latest --analysis detailed_analysis

# Available trending-crypto options:
# --category: latest, visited, gainers, losers
# --analysis: market_overview, detailed_analysis
# --dry-run: Generate without posting

# Additional commands available in app/cli/commands.py
```

## Testing

Run the test suite using pytest:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/

# Run specific test file
pytest tests/test_specific_file.py
# ie: pytest -v -s tests/services/test_crypto_service.py --no-cov

# Run tests with verbose output
pytest -v
```

Test configuration files can be found in the `tests/` directory. Make sure to create a `.env.test` file with appropriate test credentials before running the test suite.

## Project Structure

```
├── app/
│   ├── ai/
│   │   ├── agents/
│   │   │   ├── CryptoMarketAnalysisFormatAgent.py
│   │   │   └── ToneAgent.py
│   │   ├── TweetGeneratorOllama.py
│   │   ├── TweetGeneratorOpenAI.py
│   │   └── TweetGeneratorOpenRouter.py
│   ├── cli/
│   │   └── commands.py
│   ├── core/
│   │   └── exceptions.py
│   ├── services/
│   │   └── CryptoService.py
│   ├── twitter/
│   │   └── TwitterClient.py
│   └── utils/
│       └── utils.py
├── config/
│   └── prompts.py
├── tests/
│   ├── conftest.py
│   ├── test_crypto_service.py
│   └── test_twitter_client.py
├── Dockerfile
├── requirements.txt
└── run.sh
```

## Configuration

Prompt templates can be customized in `config/prompts.py`. Each AI model can be configured with different parameters and prompting strategies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Apache 2.0

## Acknowledgments

- Twitter API
- OpenAI
- Ollama
- OpenRouter
