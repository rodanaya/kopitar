"""
Test NHL API Client

Basic tests to verify API client functionality.
"""

import pytest
import asyncio
from datetime import date
from unittest.mock import AsyncMock, patch

from src.kopitar.api import NHLAPIClient
from src.kopitar.api.nhl_client import ClientConfig
from src.kopitar.api.exceptions import NHLAPIError, PlayerNotFoundError, DataValidationError


class TestNHLAPIClient:
    """Test NHL API Client functionality."""
    
    @pytest.fixture
    def client_config(self):
        """Test client configuration."""
        return ClientConfig(
            timeout=10.0,
            max_retries=2,
            cache_ttl=60,
            enable_caching=True
        )
    
    @pytest.fixture
    def client(self, client_config):
        """Test client instance."""
        return NHLAPIClient(client_config)
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initializes correctly."""
        assert client.config.timeout == 10.0
        assert client.config.max_retries == 2
        assert client.rate_limiter is not None
        assert client.cache is not None
        assert client.circuit_breaker is not None
    
    @pytest.mark.asyncio
    async def test_get_standings_mock(self, client):
        """Test standings endpoint with mocked response."""
        mock_response = {"standings": [{"teamAbbrev": {"default": "BOS"}, "wins": 50}]}

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.get_standings("2024-01-15")

            assert result == mock_response
            assert "standings" in result
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_player_not_found(self, client):
        """Test player not found handling — mock at client.get level so status_code is preserved."""
        with patch.object(client, 'get', new_callable=AsyncMock) as mock_get:
            err = NHLAPIError("Not found", status_code=404)
            err.status_code = 404
            mock_get.side_effect = err

            with pytest.raises(PlayerNotFoundError):
                await client.get_player(8999999)
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, client):
        """Test response caching works."""
        mock_response = {"test": "data"}
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            # First request
            result1 = await client.get("http://test.com/api")
            
            # Second request should use cache
            result2 = await client.get("http://test.com/api")
            
            assert result1 == result2 == mock_response
            # Should only make one actual request due to caching
            mock_request.assert_called_once()
            assert client.stats["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test rate limiting is enforced."""
        # Set very low rate limit for testing
        client.rate_limiter.config.requests_per_minute = 2
        client.rate_limiter.config.burst_size = 1
        client.rate_limiter.reset()
        
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"test": "data"}
            
            # First request should succeed immediately
            start_time = asyncio.get_event_loop().time()
            await client.get("http://test.com/api1")
            
            # Second request should be delayed due to rate limiting
            await client.get("http://test.com/api2")
            end_time = asyncio.get_event_loop().time()
            
            # Should have taken some time due to rate limiting
            assert end_time - start_time > 0.1  # At least 100ms delay
    
    @pytest.mark.asyncio
    async def test_client_stats(self, client):
        """Test client statistics tracking — mock at _http.get so _make_request runs and increments counter."""
        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"test": "data"}

        with patch.object(client._http, 'get', new_callable=AsyncMock) as mock_http:
            mock_http.return_value = mock_resp

            await client.get("http://test.com/api")
            # Second call should be a cache hit
            await client.get("http://test.com/api")

            assert client.stats["requests_made"] >= 1
            assert client.stats["cache_hits"] == 1
    
    @pytest.mark.asyncio
    async def test_season_validation(self, client):
        """Test season format validation via get_goalie_stats."""
        with pytest.raises(DataValidationError):
            await client.get_goalie_stats(season="invalid")

        with pytest.raises(DataValidationError):
            await client.get_goalie_stats(season="2023")

        # Valid season should not raise DataValidationError (may raise NHLAPIError for network)
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"data": [], "total": 0}
            try:
                await client.get_goalie_stats(season="20232024")
            except DataValidationError:
                pytest.fail("Valid season format should not raise DataValidationError")
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, client_config):
        """Test client as async context manager."""
        async with NHLAPIClient(client_config) as c:
            assert c._http is not None

        # httpx.AsyncClient is closed after context exit
        assert c._http.is_closed
    
    def test_endpoint_validation(self):
        """Test endpoint validation methods."""
        from src.kopitar.api.endpoints import NHLEndpoints
        
        # Valid seasons
        assert NHLEndpoints.validate_season("20232024") is True
        assert NHLEndpoints.validate_season("19992000") is True
        
        # Invalid seasons
        assert NHLEndpoints.validate_season("2023") is False
        assert NHLEndpoints.validate_season("20232025") is False
        assert NHLEndpoints.validate_season("invalid") is False
        
        # Valid game IDs
        assert NHLEndpoints.validate_game_id(2023020001) is True
        assert NHLEndpoints.validate_game_id(2023030417) is True
        
        # Invalid game IDs
        assert NHLEndpoints.validate_game_id(123) is False
        assert NHLEndpoints.validate_game_id(99999999999) is False


if __name__ == "__main__":
    pytest.main([__file__])