import logging
from os import getenv

import requests


LATEST_API_VERSIONS = {
    'cryptocurrency': 'v2',  # For most cryptocurrency endpoints
    'exchange': 'v1',       # For exchange-related endpoints
    'global-metrics': 'v1', # For global market metrics
    'tools': 'v1',         # For tools and utilities
    'fiat': 'v1',         # For fiat currency endpoints
    'blockchain': 'v1',    # For blockchain data
}

# Example of latest v2 endpoints
V2_ENDPOINTS = {
    'quotes': '/v2/cryptocurrency/quotes/latest',      
    'metadata': '/v2/cryptocurrency/info',            
    'market_pairs': '/v2/cryptocurrency/market-pairs/latest',
    'ohlcv': '/v2/cryptocurrency/ohlcv/latest'
}

# Some endpoints still use v1
V1_ENDPOINTS = {
    'listings': '/v1/cryptocurrency/listings/latest',
    'exchange_listings': '/v1/exchange/listings/latest',
    'global_metrics': '/v1/global-metrics/quotes/latest'
}

# Example to get specific crypto data
def get_crypto_price(symbol='BTC'):
    url = f'https://pro-api.coinmarketcap.com{V1_ENDPOINTS["listings"]}?start=1&limit=5000&convert=USD'
    parameters = {
        'symbol': symbol,
        'convert': 'USD'
    }

def get_top_crypto_coins(limit=10):
    """
    Fetch top cryptocurrencies by market cap
    
    Args:
        limit (int): Number of top coins to return (default: 10)
    
    Returns:
        list: List of dictionaries containing coin data
    """
    url = f'https://pro-api.coinmarketcap.com{V1_ENDPOINTS["listings"]}'
    
    parameters = {
        'start': 1,
        'limit': limit,
        'convert': 'USD',
        'sort': 'market_cap',
        'sort_dir': 'desc'
    }
    
    try:
        headers = {
            'X-CMC_PRO_API_KEY': getenv('COINMARKETCAP_API_KEY'),
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        
        data = response.json()
        return data['data']
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching crypto data: {str(e)}")
        return []