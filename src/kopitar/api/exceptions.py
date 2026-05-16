"""
NHL API Client Exceptions

Custom exceptions for NHL API interactions with detailed error handling.
"""

from typing import Optional, Dict, Any


class NHLAPIError(Exception):
    """Base exception for NHL API related errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(NHLAPIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class APITimeoutError(NHLAPIError):
    """Raised when API request times out."""
    
    def __init__(self, message: str = "Request timed out", timeout: Optional[float] = None):
        super().__init__(message, status_code=408)
        self.timeout = timeout


class AuthenticationError(NHLAPIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class InvalidEndpointError(NHLAPIError):
    """Raised when requesting an invalid or non-existent endpoint."""
    
    def __init__(self, endpoint: str):
        message = f"Invalid endpoint: {endpoint}"
        super().__init__(message, status_code=404)
        self.endpoint = endpoint


class DataValidationError(NHLAPIError):
    """Raised when received data fails validation."""
    
    def __init__(self, message: str, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.data = data


class SeasonNotFoundError(NHLAPIError):
    """Raised when requested season data is not available."""
    
    def __init__(self, season: str):
        message = f"Season data not found: {season}"
        super().__init__(message, status_code=404)
        self.season = season


class PlayerNotFoundError(NHLAPIError):
    """Raised when requested player is not found."""
    
    def __init__(self, player_id: int):
        message = f"Player not found: {player_id}"
        super().__init__(message, status_code=404)
        self.player_id = player_id


class GameNotFoundError(NHLAPIError):
    """Raised when requested game is not found."""
    
    def __init__(self, game_id: int):
        message = f"Game not found: {game_id}"
        super().__init__(message, status_code=404)
        self.game_id = game_id


class TeamNotFoundError(NHLAPIError):
    """Raised when requested team is not found."""
    
    def __init__(self, team_id: int):
        message = f"Team not found: {team_id}"
        super().__init__(message, status_code=404)
        self.team_id = team_id