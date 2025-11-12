import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Get the API key from environment variables
LOLLMS_KEY = os.getenv("LOLLMS_KEY")

@app.api_route("/lollms/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def lollms_proxy(request: Request, path: str):
    lollms_url = request.headers.get("X-Lollms-Url")

    if not lollms_url:
        return Response(content="X-Lollms-Url header is missing.", status_code=400)
    
    if not LOLLMS_KEY:
        return Response(content="API key is not configured on the server.", status_code=500)

    target_url = f"{lollms_url.rstrip('/')}/{path}"
    
    # Prepare headers for the forwarded request
    headers = {
        key: value for key, value in request.headers.items() 
        if key.lower() not in ['host', 'x-lollms-url', 'referer', 'accept-encoding', 'connection', 'user-agent']
    }
    headers["Authorization"] = f"Bearer {LOLLMS_KEY}"
    
    body = await request.body()
    
    # Use httpx to forward the request
    async with httpx.AsyncClient() as client:
        try:
            # A general-purpose request forwarder
            rp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body,
                timeout=300.0, # Set a reasonable timeout
            )
            
            # These headers can cause issues when streaming responses
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            response_headers = {
                name: value for name, value in rp.headers.items() if name.lower() not in excluded_headers
            }
            
            return Response(
                content=rp.content,
                status_code=rp.status_code,
                headers=response_headers,
                media_type=rp.headers.get('content-type')
            )
        except httpx.ConnectError as e:
            return Response(content=f"Failed to connect to Lollms server at {lollms_url}. Please check the URL and ensure the server is running. Error: {e}", status_code=502)
        except httpx.RequestError as e:
            return Response(content=f"Error during request to Lollms server: {e}", status_code=502)

# Mount the static files server for the frontend. This should be last.
app.mount("/", StaticFiles(directory=str(Path(__file__).parent), html=True), name="static")
