import logging
import time
from os import getenv
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """Configuration for CoinMarketCap API versions and endpoints"""
    BASE_URL: str = 'https://pro-api.coinmarketcap.com'
    VERSIONS = {
        'cryptocurrency': 'v2',  # For most cryptocurrency endpoints
        'exchange': 'v1',       # For exchange-related endpoints
        'global_metrics': 'v1', # For global market metrics
        'tools': 'v1',         # For tools and utilities
        'fiat': 'v1',          # For fiat currency endpoints
        'blockchain': 'v1',    # For blockchain data
    }

    ENDPOINTS = {
        'v2': {
            'quotes': '/v2/cryptocurrency/quotes/latest',      
            'metadata': '/v2/cryptocurrency/info',            
            'market_pairs': '/v2/cryptocurrency/market-pairs/latest',
            'ohlcv': '/v2/cryptocurrency/ohlcv/latest'
        },
        'v1': {
            'listings': '/v1/cryptocurrency/listings/latest',
            'exchange_listings': '/v1/exchange/listings/latest',
            'global_metrics': '/v1/global-metrics/quotes/latest'
        }
    }

    # Rate limits (per minute)
    RATE_LIMIT = 30
    RATE_LIMIT_WINDOW = 60  # seconds
    CALLS_PER_MINUTE = 30

class CryptoService:
    """Service for interacting with CoinMarketCap API"""
    
    def __init__(self):
        self.api_key = getenv('COINMARKETCAP_API_KEY')
        if not self.api_key:
            raise ValueError("COINMARKETCAP_API_KEY environment variable is not set")
        self.config = APIConfig()
        self._last_request_time = 0
        self._request_count = 0
        
    @sleep_and_retry
    @limits(calls=APIConfig.CALLS_PER_MINUTE, period=60)
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make authenticated request to CoinMarketCap API with rate limiting
        """
        headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }
        
        url = f'{self.config.BASE_URL}{endpoint}'
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Handle specific HTTP errors
            if response.status_code == 429:
                logger.error("Rate limit exceeded")
                raise HTTPError("Rate limit exceeded")
            elif response.status_code >= 500:
                logger.error(f"CoinMarketCap API is experiencing issues: {response.status_code}")
                raise HTTPError("API service unavailable")
                
            response.raise_for_status()
            return response.json()['data']
            
        except ConnectionError:
            logger.error("Failed to connect to CoinMarketCap API", exc_info=True)
            raise
        except Timeout:
            logger.error("Request to CoinMarketCap API timed out", exc_info=True)
            raise
        except RequestException as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_crypto_hashtags(coin_data: Dict) -> Set[str]:
        """Generate relevant hashtags for cryptocurrency data"""
        hashtags = set()
        
        # Add general crypto hashtags
        hashtags.add('#crypto')
        hashtags.add('#cryptocurrency')
        
        # Add specific coin hashtags
        if 'symbol' in coin_data:
            symbol = coin_data['symbol'].upper()
            hashtags.add(f'#{symbol}')
            if symbol == 'BTC':
                hashtags.add('#bitcoin')
            elif symbol == 'ETH':
                hashtags.add('#ethereum')
        
        # Add market condition hashtags based on 24h change
        if 'quote' in coin_data and 'USD' in coin_data['quote']:
            change_24h = coin_data['quote']['USD']['percent_change_24h']
            if change_24h > 5:
                hashtags.add('#bullish')
            elif change_24h < -5:
                hashtags.add('#bearish')
        
        return hashtags

    def get_top_crypto_coins(self, limit: int = 10) -> List[Dict]:
        """
        Fetch top cryptocurrencies by market cap with enhanced error handling
        """
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")
            
        params = {
            'start': 1,
            'limit': limit,
            'convert': 'USD',
            'sort': 'market_cap',
            'sort_dir': 'desc'
        }
        
        try:
            coins = self._make_request(self.config.ENDPOINTS['v1']['listings'], params)
            
            # Add hashtags to each coin's data
            for coin in coins:
                coin['hashtags'] = self.get_crypto_hashtags(coin)
                
            return coins
            
        except Exception as e:
            logger.error(f"Failed to fetch top crypto coins: {str(e)}")
            return []