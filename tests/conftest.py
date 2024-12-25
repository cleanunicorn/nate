import pytest
from app.services.CryptoService import CryptoService
import os
import sys

# Add project root to path if not already there
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@pytest.fixture
def crypto_service():
    return CryptoService()

@pytest.fixture
def mock_market_data():
    return [
        {
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'current_price': 50000,
            'market_cap': 1000000000000,
            'total_volume': 50000000000,
            'price_change_percentage_24h': 5.5,
            'market_cap_rank': 1,
            'roi': None
        }
    ] 