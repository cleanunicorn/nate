import logging
from os import getenv
from typing import List, Dict, Optional, Set, Literal
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

CategoryType = Literal['latest', 'visited', 'gainers', 'losers']

@dataclass
class APIConfig:
    """Configuration for CoinGecko API endpoints"""
    BASE_URL: str = 'https://api.coingecko.com/api/v3'
    CALLS_PER_MINUTE = 50
    RATE_LIMIT = 50
    RATE_LIMIT_WINDOW = 60  # seconds
    
    ENDPOINTS = {
        'trending': '/search/trending',
        'markets': '/coins/markets',
        'global': '/global'
    }

class CryptoService:
    """Service for interacting with CoinGecko API"""
    
    def __init__(self):
        self.api_key = getenv('COINGECKO_API_KEY')
        if not self.api_key:
            raise ValueError("COINGECKO_API_KEY environment variable is not set")
        self.config = APIConfig()

    @sleep_and_retry
    @limits(calls=APIConfig.CALLS_PER_MINUTE, period=APIConfig.RATE_LIMIT_WINDOW)
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to CoinGecko API with rate limiting"""
        url = f'{self.config.BASE_URL}{endpoint}'
        headers = {'X-Cg-demo-Api-Key': self.api_key}
        
        try:
            response = requests.get(
                url, 
                headers=headers,
                params=params, 
                timeout=10
            )
            
            if response.status_code == 400:
                logger.error(f"Bad Request: Invalid parameters - URL: {url}, Params: {params}")
                raise HTTPError(f"Bad Request: Invalid parameters for endpoint {endpoint}")
            elif response.status_code == 429:
                logger.error("Rate limit exceeded")
                raise HTTPError("Rate limit exceeded")
            elif response.status_code == 401:
                logger.error("Unauthorized: Invalid API key")
                raise HTTPError("Unauthorized: Invalid API key")
            elif response.status_code == 403:
                logger.error("Forbidden: API key doesn't have access to this endpoint")
                raise HTTPError("Forbidden: API key doesn't have access to this endpoint")
            elif response.status_code >= 500:
                logger.error(f"CoinGecko API is experiencing issues: {response.status_code}")
                raise HTTPError("API service unavailable")
                
            response.raise_for_status()
            return response.json()
            
        except ConnectionError:
            logger.error("Failed to connect to CoinGecko API", exc_info=True)
            raise
        except Timeout:
            logger.error("Request to CoinGecko API timed out", exc_info=True)
            raise
        except RequestException as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            raise

    @sleep_and_retry
    @limits(calls=APIConfig.CALLS_PER_MINUTE, period=APIConfig.RATE_LIMIT_WINDOW)
    def get_trending_coins(self, category: CategoryType = 'latest', limit: int = 10) -> List[Dict]:
        """
        Fetch trending cryptocurrencies based on specified category
        """
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")

        try:
            if category == 'latest':
                # Get trending coins
                data = self._make_request(self.config.ENDPOINTS['trending'])
                coins = [item['item'] for item in data['coins']][:limit]
                
                # Get additional market data for these coins
                coin_ids = [coin['id'] for coin in coins]
                return self._get_market_data(coin_ids)
                
            else:  # visited, gainers, losers
                params = {
                    'vs_currency': 'usd',
                    'per_page': '250',  # Get more coins to sort through
                    'page': '1',
                    'order': 'market_cap_desc',
                    'sparkline': 'false',
                    'price_change_percentage': '24h'
                }
                
                data = self._make_request(self.config.ENDPOINTS['markets'], params)
                
                if category == 'visited':
                    data.sort(key=lambda x: float(x.get('total_volume', 0) or 0), reverse=True)
                elif category == 'gainers':
                    data.sort(key=lambda x: float(x.get('price_change_percentage_24h', 0) or 0), reverse=True)
                elif category == 'losers':
                    data.sort(key=lambda x: float(x.get('price_change_percentage_24h', 0) or 0))
                
                return self._format_coins(data[:limit])
            
        except Exception as e:
            logger.error(f"Failed to fetch trending coins: {str(e)}")
            return []

    def _get_market_data(self, coin_ids: List[str]) -> List[Dict]:
        """Get detailed market data for specific coins"""
        # First, ensure we have valid coin IDs
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(coin_ids),
            'sparkline': 'false'  # Removed price_change_percentage to simplify request
        }
        
        try:
            logger.debug(f"Making request with params: {params}")  # Debug log
            coins = self._make_request(self.config.ENDPOINTS['markets'], params)
            return self._format_coins(coins)
        except Exception as e:
            logger.error(f"Failed to fetch market data: {str(e)}")
            return []

    def _format_coins(self, coins: List[Dict]) -> List[Dict]:
        """Format coin data and add hashtags"""
        formatted_coins = []
        for coin in coins:
            try:
                formatted_coin = {
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'quote': {
                        'USD': {
                            'price': float(coin['current_price'] or 0),
                            'percent_change_24h': float(coin.get('price_change_percentage_24h', 0) or 0),
                            'volume_24h': float(coin.get('total_volume', 0) or 0),
                            'market_cap': float(coin.get('market_cap', 0) or 0)
                        }
                    }
                }
                formatted_coin['hashtags'] = self.get_crypto_hashtags(formatted_coin)
                formatted_coins.append(formatted_coin)
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error formatting coin data: {e}")
                continue
                
        return formatted_coins

    @sleep_and_retry
    @limits(calls=APIConfig.CALLS_PER_MINUTE, period=APIConfig.RATE_LIMIT_WINDOW)
    def get_top_crypto_coins(self, limit: int = 10) -> List[Dict]:
        """Fetch top cryptocurrencies by market cap"""
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