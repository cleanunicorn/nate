import logging
from os import getenv
from typing import List, Dict, Optional, Set, Literal, Any
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from ratelimit import limits, sleep_and_retry
from config.api_config import APIConfig
from app.core.exceptions import (
    CryptoAPIError,
    RateLimitError,
    DataFormatError,
    CoinLimitError,
    MarketDataError,
    UnauthorizedError,
    ServerError
)

CategoryType = Literal['latest', 'visited', 'gainers', 'losers']
TRENDING_COINS_LIMIT = 3

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
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            elif e.response.status_code == 400:
                raise CryptoAPIError(f"Bad Request: Invalid parameters for endpoint {endpoint}") from e
            elif e.response.status_code == 401:
                raise UnauthorizedError("Invalid API key") from e
            elif e.response.status_code == 403:
                raise UnauthorizedError("API key doesn't have access to this endpoint") from e
            elif e.response.status_code >= 500:
                raise ServerError("API service unavailable") from e
            raise
        except ConnectionError:
            raise ConnectionError("Failed to connect to CoinGecko API")
        except Timeout:
            raise Timeout("Request to CoinGecko API timed out")
        except RequestException as e:
            raise RequestException(f"API request failed: {str(e)}") from e

    @sleep_and_retry
    @limits(
        calls=APIConfig.COINGECKO_CALLS_PER_MINUTE,
        period=APIConfig.COINGECKO_RATE_LIMIT_WINDOW
    )
    def get_search_trending_coins(
        self,
        limit: int = TRENDING_COINS_LIMIT
    ) -> List[Dict[str, Any]]:
        """Fetch trending cryptocurrencies from the search/trending endpoint.
        
        Args:
            limit (int, optional): Maximum number of coins to return. Defaults to TRENDING_COINS_LIMIT.
            
        Returns:
            List[Dict[str, Any]]: List of trending coins with market data
            
        Raises:
            CoinLimitError: If limit is invalid
            RateLimitError: If API rate limit is exceeded
            CryptoAPIError: If API request fails
            DataFormatError: If response format is invalid
        """
        if not isinstance(limit, int) or limit < 1:
            raise CoinLimitError("Limit must be a positive integer")
        if limit > TRENDING_COINS_LIMIT:
            raise CoinLimitError(f"Limit cannot exceed {TRENDING_COINS_LIMIT}")

        try:
            data = self._fetch_trending_search_coins(limit)
            if not data:
                raise MarketDataError("No trending coins data received")
            return data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            raise CryptoAPIError(f"API request failed: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise CryptoAPIError(f"Request failed: {str(e)}") from e
        except (KeyError, ValueError) as e:
            raise DataFormatError(f"Invalid data format: {str(e)}") from e

    @sleep_and_retry
    @limits(
        calls=APIConfig.COINGECKO_CALLS_PER_MINUTE,
        period=APIConfig.COINGECKO_RATE_LIMIT_WINDOW
    )
    def get_market_trending_coins(
        self,
        category: Literal['visited', 'gainers', 'losers'],
        limit: int = TRENDING_COINS_LIMIT
    ) -> List[Dict[str, Any]]:
        """Fetch trending cryptocurrencies from the coins/markets endpoint.
        
        Args:
            category: Type of market data to fetch ('visited', 'gainers', 'losers')
            limit: Maximum number of coins to return (default: 3)
            
        Returns:
            List of formatted coin data sorted by the specified category.
            
        Raises:
            CoinLimitError: If limit is invalid
            RateLimitError: If API rate limit is exceeded
            CryptoAPIError: If API request fails
            DataFormatError: If response format is invalid
        """
        if not isinstance(limit, int) or limit < 1:
            raise CoinLimitError("Limit must be a positive integer")
        if limit > TRENDING_COINS_LIMIT:
            raise CoinLimitError(f"Limit cannot exceed {TRENDING_COINS_LIMIT}")

        try:
            return self._fetch_market_coins_by_category(category, limit)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            raise CryptoAPIError(f"API request failed: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise CryptoAPIError(f"Request failed: {str(e)}") from e
        except (KeyError, ValueError) as e:
            raise DataFormatError(f"Invalid data format: {str(e)}") from e

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
            MarketDataError: If market data fetch fails
            DataFormatError: If response format is invalid
        """
        try:
            market_data = self._fetch_raw_market_data()
            if not market_data:
                raise MarketDataError("No market data received")
                
            sorted_data = self._sort_market_data(market_data, category)
            return self._format_coins(sorted_data[:limit])
            
        except Exception as e:
            raise MarketDataError(f"Failed to fetch market data: {str(e)}") from e

    def _fetch_raw_market_data(self) -> List[Dict[str, Any]]:
        """Fetch raw market data from the API."""
        params = {
            'vs_currency': 'usd',
            'per_page': '250',  # Get more coins to sort through
            'page': '1',
            'order': 'market_cap_desc',
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        return self._make_request(self.config.ENDPOINTS['markets'], params)

    def _sort_market_data(
        self,
        market_data: List[Dict[str, Any]],
        category: Literal['visited', 'gainers', 'losers']
    ) -> List[Dict[str, Any]]:
        """Sort market data based on category."""
        if category == 'visited':
            return self._sort_by_volume(market_data)
        return self._sort_by_price_change(market_data, reverse=category=='gainers')

    def _sort_by_volume(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort data by trading volume, higher volume first."""
        return sorted(
            data,
            key=lambda x: float(x.get('total_volume', 0) or 0),
            reverse=True  # Higher volume first
        )

    def _sort_by_price_change(
        self,
        data: List[Dict[str, Any]],
        reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """Sort data by price change percentage.
        
        Args:
            data: List of coin data to sort
            reverse: If True, sort gainers (high to low), if False, sort losers (low to high)
        """
        return sorted(
            data,
            key=lambda x: float(x.get('price_change_percentage_24h', 0) or 0),
            reverse=reverse
        )

    def _get_market_data(self, coin_ids: List[str]) -> List[Dict]:
        """Get detailed market data for specific coins.
        
        Raises:
            CryptoAPIError: If API request fails
            DataFormatError: If response format is invalid
        """
        params = {
            'vs_currency': 'usd',
            'ids': ','.join(coin_ids),
            'order': 'market_cap_desc',
            'price_change_percentage': '24h'
        }
        
        try:
            coins = self._make_request(self.config.ENDPOINTS['markets'], params)
            if not coins:
                raise DataFormatError("No coin data received")
            return self._format_coins(coins)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError("Rate limit exceeded") from e
            raise CryptoAPIError(f"API request failed: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            raise CryptoAPIError(f"Request failed: {str(e)}") from e
        except (KeyError, ValueError) as e:
            raise DataFormatError(f"Invalid data format: {str(e)}") from e

    def _format_coins(self, coins: List[Dict]) -> List[Dict]:
        """Format coin data and add hashtags.
        
        Raises:
            DataFormatError: If coin data format is invalid
        """
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
                raise DataFormatError(f"Error formatting coin data: {e}") from e
                
        if not formatted_coins:
            raise DataFormatError("Failed to format any coin data")
            
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