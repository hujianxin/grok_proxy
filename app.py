import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with file output and rotation
import logging.handlers
import os.path

log_dir = os.getenv('LOG_DIR', os.path.join(os.getcwd(), 'logs'))
log_file = os.path.join(log_dir, 'grok_proxy.log')
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Create formatter
formatter = logging.Formatter(os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create file handler with rotation (max 2 days)
file_handler = logging.handlers.TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=2
)
file_handler.setFormatter(formatter)
file_handler.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# Add handlers to logger
logger.handlers = [file_handler, console_handler]

# Constants
GROK_API_BASE_URL = "https://api.x.ai/v1"
GROK_CHAT_COMPLETIONS_URL = f"{GROK_API_BASE_URL}/chat/completions"
GROK_MODELS_URL = f"{GROK_API_BASE_URL}/models"
TIMEOUT = float(os.getenv('PROXY_TIMEOUT', '30'))

app = FastAPI()

def validate_auth_header(request: Request) -> str:
    """Validate and return the Authorization header from the request."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    return auth_header

async def stream_response(response: httpx.Response) -> StreamingResponse:
    """Stream the response content back to the client."""
    async def generate():
        async for chunk in response.aiter_bytes():
            yield chunk
    return StreamingResponse(
        generate(),
        media_type="application/json",
        status_code=response.status_code
    )

async def handle_http_request(client: httpx.AsyncClient, url: str, method: str = 'POST', json: dict = None, headers: dict = None) -> StreamingResponse:
    """Handle HTTP request to Grok API with error handling."""
    try:
        if method == 'POST':
            response = await client.post(url, json=json, headers=headers)
        else:  # GET
            response = await client.get(url, headers=headers)
        response.raise_for_status()
        return await stream_response(response) if method == 'POST' else response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Grok API error: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def forward_request_to_grok(request: Request):
    """Forward the incoming request to Grok API with streaming response."""
    auth_header = validate_auth_header(request)
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
        raise HTTPException(status_code=400, detail="Invalid request body")

    logger.info(f"Forwarding request to Grok API: {body}")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        return await handle_http_request(client, GROK_CHAT_COMPLETIONS_URL, 'POST', body, headers)

@app.post("/v1/chat/completions")
async def proxy_chat_completions(request: Request):
    """Proxy endpoint for chat completions."""
    return await forward_request_to_grok(request)

@app.get("/v1/models")
async def get_models(request: Request):
    """Endpoint to retrieve available models from Grok API."""
    auth_header = validate_auth_header(request)
    
    headers = {
        'Authorization': auth_header,
        'Accept': 'application/json'
    }
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        return await handle_http_request(client, GROK_MODELS_URL, 'GET', headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
