import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
app = FastAPI()

# Retrieve the Lollms API key from environment variables
LOLLMS_KEY = os.getenv("LOLLMS_KEY")

@app.api_route("/lollms/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def lollms_proxy(request: Request, path: str):
    """
    A secure proxy endpoint to forward requests to the main Lollms server.
    """
    # Get the target Lollms server URL from the custom header sent by the frontend.
    lollms_url = request.headers.get("X-Lollms-Url")
    if not lollms_url:
        return Response(content="X-Lollms-Url header is missing.", status_code=400)

    # Construct the full target URL for the Lollms API endpoint.
    target_url = f"{lollms_url.rstrip('/')}/{path}"

    # Prepare headers for the forwarded request.
    # We remove host-related headers and add the mandatory Authorization header.
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'x-lollms-url', 'referer']}
    if LOLLMS_KEY:
        headers["Authorization"] = f"Bearer {LOLLMS_KEY}"
    else:
        return Response(content="LOLLMS_KEY is not set on the server.", status_code=500)
        
    # Use httpx to create an asynchronous client and forward the request.
    async with httpx.AsyncClient() as client:
        try:
            # Forward the request with the same method, headers, query params, and body.
            rp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
                timeout=300.0,
            )
            # Return the response from the Lollms server directly to the frontend.
            return Response(content=rp.content, status_code=rp.status_code, headers=rp.headers)
        except httpx.RequestError as e:
            # Handle potential connection errors to the Lollms server.
            return Response(content=f"Error connecting to Lollms server: {e}", status_code=502)

# Mount the static file server to serve the frontend (index.html and other assets).
# This must be the last part of the file.
app.mount("/", StaticFiles(directory=str(Path(__file__).parent), html=True), name="static")