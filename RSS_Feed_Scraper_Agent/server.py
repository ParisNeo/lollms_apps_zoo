import sys
import pipmaster as pm

# Check and install required packages
required_packages = [
    ["fastapi", "", None],
    ["uvicorn", "", None],
    ["feedparser", "", None],
    ["aiohttp", "", None],
    ["pydantic", "", None],
    ["fastapi-cors", "", None]  # Add this new package for CORS support
]

for package, min_version, index_url in required_packages:
    if not pm.is_installed(package):
        pm.install_or_update(package, index_url)
    else:
        if min_version:
            if pm.get_installed_version(package) < min_version:
                pm.install_or_update(package, index_url)

# Now that we've ensured all packages are installed, we can import them
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import feedparser
from typing import List
import asyncio
import aiohttp

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9600"],  # Allow only localhost:9600
    allow_credentials=True,
    allow_methods=["*"],  # You can restrict this to specific HTTP methods if needed
    allow_headers=["*"],  # You can restrict this to specific headers if needed
)

class RSSRequest(BaseModel):
    urls: List[str]

class RSSItem(BaseModel):
    title: str
    link: str
    description: str
    published: str

class RSSResponse(BaseModel):
    feed_url: str
    items: List[RSSItem]

async def fetch_rss(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.text()
                feed = feedparser.parse(content)
                items = []
                for entry in feed.entries[:10]:  # Limit to 10 most recent items
                    items.append(RSSItem(
                        title=entry.get('title', ''),
                        link=entry.get('link', ''),
                        description=entry.get('description', ''),
                        published=entry.get('published', '')
                    ))
                return RSSResponse(feed_url=url, items=items)
            else:
                return RSSResponse(feed_url=url, items=[])
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return RSSResponse(feed_url=url, items=[])

@app.post("/get_rss_content")
async def get_rss_content(request: RSSRequest):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_rss(session, url) for url in request.urls]
        results = await asyncio.gather(*tasks)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
