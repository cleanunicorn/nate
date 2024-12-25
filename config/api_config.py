"""Configuration module for API settings."""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class APIConfig:
    """Configuration settings for CoinGecko API.
    
    Attributes:
        COINGECKO_BASE_URL: Base URL for the CoinGecko API.
        COINGECKO_CALLS_PER_MINUTE: Maximum number of API calls allowed per minute.
        COINGECKO_RATE_LIMIT: Rate limit threshold.
        COINGECKO_RATE_LIMIT_WINDOW: Time window in seconds for rate limiting.
        ENDPOINTS: Dictionary of API endpoint paths.
    """
    
    COINGECKO_BASE_URL: str = 'https://api.coingecko.com/api/v3'
    COINGECKO_CALLS_PER_MINUTE: int = 50
    COINGECKO_RATE_LIMIT: int = 50
    COINGECKO_RATE_LIMIT_WINDOW: int = 60
    COINGECKO_TIMEOUT: int = 10

    
    ENDPOINTS: Dict[str, str] = field(
        default_factory=lambda: {
            'trending': '/search/trending',
            'markets': '/coins/markets',
            'global': '/global'
        }
    )