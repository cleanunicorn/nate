class AIGenerationError(Exception):
    """Raised when AI generation fails"""
    pass

class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)

class UnauthorizedError(APIError):
    """Raised when API request is unauthorized"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ServerError(APIError):
    """Raised when API server returns an error"""
    def __init__(self, message: str = "Server error"):
        super().__init__(message, status_code=500)

class CryptoServiceError(Exception):
    """Base exception for crypto service errors."""
    pass

class CryptoAPIError(CryptoServiceError):
    """Raised when there's an API-related error."""
    pass

class RateLimitError(CryptoAPIError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message)

class DataFormatError(CryptoServiceError):
    """Raised when data doesn't match expected format."""
    pass

class CoinLimitError(CryptoServiceError):
    """Raised when coin limit is exceeded or not met."""
    pass

class MarketDataError(CryptoServiceError):
    """Raised when market data is invalid or missing."""
    pass

class TweetGenerationError(Exception):
    """Raised when tweet generation fails."""
    pass

class TweetFormatError(TweetGenerationError):
    """Raised when generated tweet doesn't match required format."""
    pass 