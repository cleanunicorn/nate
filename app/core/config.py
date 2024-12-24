from typing import Dict, ClassVar
from pydantic import BaseModel

class APIConfig(BaseModel):
    """API Configuration"""
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    COINGECKO_CALLS_PER_MINUTE: int = 30
    COINGECKO_RATE_LIMIT_WINDOW: int = 60  # seconds
    COINGECKO_TIMEOUT: int = 10
    
    ENDPOINTS: ClassVar[Dict[str, str]] = {
        'trending': '/search/trending',
        'markets': '/coins/markets',
        'global': '/global'
    } 