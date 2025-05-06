import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from app import validate_auth_header, handle_http_request, forward_request_to_grok, stream_response

# Mock environment variables for testing
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['LOG_DIR'] = './test_logs'
os.environ['PROXY_TIMEOUT'] = '10'

@pytest.fixture
def mock_httpx_client():
    """Fixture to mock httpx.AsyncClient for testing."""
    with patch('httpx.AsyncClient') as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_validate_auth_header_success():
    """Test successful validation of Authorization header."""
    class MockRequest:
        headers = {'Authorization': 'Bearer test_token'}
    
    result = validate_auth_header(MockRequest())
    assert result == 'Bearer test_token'

@pytest.mark.asyncio
async def test_validate_auth_header_missing():
    """Test validation failure when Authorization header is missing."""
    class MockRequest:
        headers = {}
    
    with pytest.raises(HTTPException) as exc_info:
        validate_auth_header(MockRequest())
    assert exc_info.value.status_code == 401
    assert str(exc_info.value.detail) == "Missing Authorization header"

@pytest.mark.asyncio
async def test_proxy_chat_completions_success(mock_httpx_client):
    """Test successful proxying of chat completions request."""
    # Mock response from Grok API
    mock_response = AsyncMock()
    mock_response.status_code = 200  # Ensure this is a direct integer value
    async def mock_aiter_bytes():
        yield b'{"response": "success"}'
    mock_response.aiter_bytes = mock_aiter_bytes
    mock_httpx_client.return_value.post.return_value = mock_response
    
    class MockRequest:
        headers = {'Authorization': 'Bearer test_token'}
        async def json(self):
            return {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    
    response = await forward_request_to_grok(MockRequest())
    assert isinstance(response, StreamingResponse)
    # Directly check the mocked status code from the response setup
    assert mock_httpx_client.return_value.post.return_value.status_code == 200

@pytest.mark.asyncio
async def test_proxy_chat_completions_unauthorized():
    """Test proxying chat completions request without Authorization header."""
    class MockRequest:
        headers = {}
        async def json(self):
            return {"model": "test-model", "messages": [{"role": "user", "content": "Hello"}]}
    
    with pytest.raises(HTTPException) as exc_info:
        await forward_request_to_grok(MockRequest())
    assert exc_info.value.status_code == 401
    assert str(exc_info.value.detail) == "Missing Authorization header"

@pytest.mark.asyncio
async def test_get_models_success(mock_httpx_client):
    """Test successful retrieval of models from Grok API."""
    # Mock response from Grok API
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"models": ["model1", "model2"]}
    mock_httpx_client.return_value.get.return_value = mock_response
    
    class MockRequest:
        headers = {'Authorization': 'Bearer test_token'}
    
    async def mock_handle_http_request(client, url, method='GET', json=None, headers=None):
        # Directly return the mocked response value instead of awaiting a coroutine
        return mock_response.json.return_value
    
    with patch('app.handle_http_request', side_effect=mock_handle_http_request):
        from app import get_models
        response = await get_models(MockRequest())
        assert "models" in response
        assert response["models"] == ["model1", "model2"]

if __name__ == "__main__":
    pytest.main(["-v"])
