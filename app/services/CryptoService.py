import logging
from os import getenv
from typing import List, Dict, Optional, Set, Literal, Any
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from ratelimit import limits, sleep_and_retry
from config.api_config import APIConfig

logger = logging.getLogger(__name__)

CategoryType = Literal['latest', 'visited', 'gainers', 'losers']

class CryptoService:
    """Service for interacting with CoinGecko API."""
    
    def __init__(self, api_config: Optional[APIConfig] = None) -> None:
        """Initialize CoinGecko API client.
        
        Args:
            api_config: Configuration for API calls. If None, uses default values.
            
        Raises:
            ValueError: If COINGECKO_API_KEY environment variable is not set.
        """
        self.config = api_config or APIConfig()
        self.base_url = self.config.COINGECKO_BASE_URL
        self.api_key = getenv('COINGECKO_API_KEY')
        if not self.api_key:
            raise ValueError("COINGECKO_API_KEY environment variable is not set")

    @sleep_and_retry
    @limits(calls=APIConfig.COINGECKO_CALLS_PER_MINUTE, period=APIConfig.COINGECKO_RATE_LIMIT_WINDOW)
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make authenticated request to CoinGecko API with rate limiting.
        
        Args:
            endpoint: API endpoint to call.
            params: Query parameters for the request.
            
        Returns:
            Optional[Dict[str, Any]]: JSON response from the API.
            
        Raises:
            HTTPError: For various HTTP-related errors.
            ConnectionError: When connection fails.
            Timeout: When request times out.
            RequestException: For other request-related errors.
        """
        url = f'{self.base_url}{endpoint}'
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
    @limits(
        calls=APIConfig.COINGECKO_CALLS_PER_MINUTE,
        period=APIConfig.COINGECKO_RATE_LIMIT_WINDOW
    )
    def get_search_trending_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch trending cryptocurrencies from the search/trending endpoint.
        
        Args:
            limit: Maximum number of coins to return.
            
        Returns:
            List of formatted coin data.
            
        Raises:
            ValueError: If limit is not a positive integer.
        """
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")

        try:
            return self._fetch_trending_search_coins(limit)
        except Exception as e:
            logger.error(f"Failed to fetch search trending coins: {str(e)}")
            raise

    @sleep_and_retry
    @limits(
        calls=APIConfig.COINGECKO_CALLS_PER_MINUTE,
        period=APIConfig.COINGECKO_RATE_LIMIT_WINDOW
    )
    def get_market_trending_coins(
        self,
        category: Literal['visited', 'gainers', 'losers'],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch trending cryptocurrencies from the coins/markets endpoint.
        
        Args:
            category: Type of market data to fetch ('visited', 'gainers', 'losers').
            limit: Maximum number of coins to return.
            
        Returns:
            List of formatted coin data sorted by the specified category.
            
        Raises:
            ValueError: If limit is not a positive integer.
        """
        if not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer")

        try:
            return self._fetch_market_coins_by_category(category, limit)
        except Exception as e:
            logger.error(f"Failed to fetch market trending coins: {str(e)}")
            raise

    def _fetch_trending_search_coins(self, limit: int) -> List[Dict[str, Any]]:
        """Fetch trending coins using the /search/trending endpoint.
        
        Args:
            limit: Maximum number of coins to return.
            
        Returns:
            List of formatted coin data for trending coins.
            
        Raises:
            Exception: If trending coins fetch fails.
        """
        data = self._make_request(self.config.ENDPOINTS['trending'])
        coins = [item['item'] for item in data['coins']][:limit]
        coin_ids = [coin['id'] for coin in coins]
        return self._get_market_data(coin_ids)

    def _fetch_market_coins_by_category(
        self,
        category: Literal['visited', 'gainers', 'losers'],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch and sort coins using the /coins/markets endpoint.
        
        Args:
            category: Type of market data to fetch ('visited', 'gainers', 'losers').
            limit: Maximum number of coins to return.
            
        Returns:
            List of formatted coin data sorted by the specified category.
            
        Raises:
            Exception: If market data fetch fails.
        """
        params = {
            'vs_currency': 'usd',
            'per_page': '250',  # Get more coins to sort through
            'page': '1',
            'order': 'market_cap_desc',
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        
        market_data = self._make_request(self.config.ENDPOINTS['markets'], params)
        
        sort_key_map = {
            'visited': lambda x: float(x.get('total_volume', 0) or 0),
            'gainers': lambda x: float(x.get('price_change_percentage_24h', 0) or 0),
            'losers': lambda x: float(x.get('price_change_percentage_24h', 0) or 0)
        }
        
        reverse_sort = category != 'losers'
        market_data.sort(key=sort_key_map[category], reverse=reverse_sort)
        
        return self._format_coins(market_data[:limit])

    def _get_market_data(self, coin_ids: List[str]) -> List[Dict]:
        """Get detailed market data for specific coins"""
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(coin_ids),
            'order': 'market_cap_desc',
            'price_change_percentage': '24h'
        }
        
        try:
            coins = self._make_request(self.config.ENDPOINTS['markets'], params)
            return self._format_coins(coins)
        except Exception as e:
            logger.error(f"Failed to fetch market data: {str(e)}")
            raise e

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