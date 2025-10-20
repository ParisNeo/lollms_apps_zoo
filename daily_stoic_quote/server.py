import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Setup for serving static files and templates
current_file_path = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_file_path / "templates"))


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Main endpoint to fetch a stoic quote and render it on the page.
    """
    api_url = os.getenv("STOIC_API_URL")
    quote_data = {
        "quote": "Failed to fetch a quote. Please check the API URL in the .env file.",
        "author": "System"
    }

    if not api_url:
        quote_data["quote"] = "STOIC_API_URL is not defined in the .env file."
    else:
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            
            # The API returns a dictionary, let's format it for display
            # Example response: {"quote": "The best revenge is to be unlike him who performed the injury.", "author": "Marcus Aurelius"}
            if "quote" in data and "author" in data:
                quote_data = {
                    "quote": data["quote"],
                    "author": data["author"]
                }

        except requests.exceptions.RequestException as e:
            quote_data["quote"] = f"Error connecting to the API: {e}"
        except Exception as e:
            quote_data["quote"] = f"An unexpected error occurred: {e}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "quote": quote_data["quote"],
        "author": quote_data["author"]
    })

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 9601))
    uvicorn.run(app, host=host, port=port)