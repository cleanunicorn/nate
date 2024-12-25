from unittest.mock import Mock, patch
import pytest
from pytest_check import check
import requests
from app.services.CryptoService import CryptoService
from config.api_config import APIConfig

class TestCryptoService:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize service with API config"""
        self.api_config = APIConfig(
            COINGECKO_BASE_URL="https://api.coingecko.com/api/v3",
            COINGECKO_CALLS_PER_MINUTE=30,
            COINGECKO_RATE_LIMIT_WINDOW=1,  # Use shorter window for tests
            COINGECKO_TIMEOUT=10
        )
        self.service = CryptoService(api_config=self.api_config)
        
        # Create a patcher for all requests
        self.requests_patcher = patch('requests.get')
        self.mock_get = self.requests_patcher.start()
        
    def teardown_method(self):
        """Stop request patching after each test"""
        self.requests_patcher.stop()

    def test_get_search_trending_coins(self):
        """Test fetching trending coins from search endpoint"""
        # First request for trending
        trending_response = Mock(status_code=200)
        trending_response.json.return_value = {
            'coins': [{
                'item': {
                    'id': 'bitcoin',
                    'coin_id': 1,
                    'name': 'Bitcoin',
                    'symbol': 'BTC',
                    'market_cap_rank': 1,
                    'thumb': 'thumb_url',
                    'small': 'small_url',
                    'large': 'large_url',
                    'slug': 'bitcoin',
                    'price_btc': 1.0,
                    'score': 0
                }
            }]
        }
        
        # Second request for market data
        market_response = Mock(status_code=200)
        market_response.json.return_value = [{
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'image': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
            'current_price': 50000.0,
            'market_cap': 1000000000000,
            'market_cap_rank': 1,
            'total_volume': 50000000000,
            'price_change_percentage_24h': 5.5,
            'sparkline_in_7d': {'price': []}
        }]
        
        self.mock_get.side_effect = [trending_response, market_response]
        
        result = self.service.get_search_trending_coins()
        
        with check:
            check.is_true(isinstance(result, list))
            check.is_true(len(result) > 0)
            if len(result) > 0:
                # Check formatted fields
                check.equal(result[0]['name'], 'Bitcoin')
                check.equal(result[0]['symbol'], 'BTC')
                check.equal(result[0]['quote']['USD']['price'], 50000.0)
                check.equal(result[0]['quote']['USD']['market_cap'], 1000000000000)
                check.equal(result[0]['quote']['USD']['volume_24h'], 50000000000)
                check.equal(result[0]['quote']['USD']['percent_change_24h'], 5.5)
        
    def test_get_market_trending_coins_visited(self):
        """Test fetching most visited coins from markets endpoint"""
        visited_markets_response = Mock(status_code=200)
        visited_markets_response.json.return_value = [{
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'image': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
            'current_price': 50000.0,
            'market_cap': 1000000000000,
            'market_cap_rank': 1,
            'total_volume': 50000000000,
            'price_change_percentage_24h': 5.5,
            'sparkline_in_7d': {'price': []}
        }]
        
        self.mock_get.return_value = visited_markets_response
        result = self.service.get_market_trending_coins(category='visited')
        
        with check:
            check.is_true(isinstance(result, list))
            check.is_true(len(result) > 0)
            if len(result) > 0:
                coin = result[0]
                volume_24h = coin['quote']['USD']['volume_24h']
                check.greater(volume_24h, 0)
        
    def test_get_market_trending_coins_gainers(self):
        """Test fetching top gainers from markets endpoint"""
        gainers_markets_response = Mock(status_code=200)
        gainers_markets_response.json.return_value = [{
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'image': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
            'current_price': 50000.0,
            'market_cap': 1000000000000,
            'market_cap_rank': 1,
            'total_volume': 50000000000,
            'price_change_percentage_24h': 5.5,
            'sparkline_in_7d': {'price': []}
        }]
        
        self.mock_get.return_value = gainers_markets_response
        result = self.service.get_market_trending_coins(category='gainers')
        
        with check:
            check.is_true(isinstance(result, list))
            check.is_true(len(result) > 0)
            if len(result) > 0:
                coin = result[0]
                percent_change = coin['quote']['USD']['percent_change_24h']
                check.greater(percent_change, 0)
        
    def test_get_market_trending_coins_losers(self):
        """Test fetching top losers from markets endpoint"""
        losers_markets_response = Mock(status_code=200)
        losers_markets_response.json.return_value = [{
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'image': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
            'current_price': 50000.0,
            'market_cap': 1000000000000,
            'market_cap_rank': 1,
            'total_volume': 50000000000,
            'price_change_percentage_24h': -5.5,
            'sparkline_in_7d': {'price': []}
        }]
        
        self.mock_get.return_value = losers_markets_response
        result = self.service.get_market_trending_coins(category='losers')
        
        with check:
            check.is_true(isinstance(result, list))
            check.is_true(len(result) > 0)
            if len(result) > 0:
                coin = result[0]
                percent_change = coin['quote']['USD']['percent_change_24h']
                check.less(percent_change, 0)
            
    def test_rate_limit_handling(self):
        """Test handling of rate limit errors"""
        mock_response = Mock(status_code=429)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=Mock(status_code=429)
        )
        self.mock_get.return_value = mock_response
        
        with pytest.raises(requests.exceptions.RequestException) as exc_info:
            self.service.get_search_trending_coins()
        check.is_in("Rate limit exceeded", str(exc_info.value))