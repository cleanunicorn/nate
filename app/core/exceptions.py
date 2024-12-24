class AIGenerationError(Exception):
    """Raised when AI generation fails"""
    pass

class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)

class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)

class UnauthorizedError(APIError):
    """Raised when API request is unauthorized"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ServerError(APIError):
    """Raised when API server returns an error"""
    def __init__(self, message: str = "Server error"):
        super().__init__(message, status_code=500) 