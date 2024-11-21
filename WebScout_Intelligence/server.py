from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin, urlparse
import tiktoken
import logging
from lollms_client import LollmsClient

lc = LollmsClient()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class ScrapeRequest(BaseModel):
    urls: List[str]
    depth: int = 1

class ProcessRequest(BaseModel):
    text: str
    chunk_size: int = 4096

class SubjectUpdateRequest(BaseModel):
    chunk: str
    current_subjects: List[str]

# Global variables
STORAGE_DIR = "data"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Helper Functions
def save_state(filename: str, data: dict):
    with open(os.path.join(STORAGE_DIR, filename), 'w', encoding='utf-8') as f:
        json.dump(data, f)

def load_state(filename: str) -> dict:
    try:
        with open(os.path.join(STORAGE_DIR, filename), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.error(f"Failed to fetch {url}: {response.status}")
                return ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return ""

def extract_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    text_elements = []
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span']):
        text_elements.append(tag.get_text().strip())
    return "\n".join(filter(None, text_elements))

def extract_links(html_content: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.append(full_url)
    return links

def tokenize_text(text: str) -> List[int]:
    encoding = tiktoken.get_encoding("cl100k_base")
    return encoding.encode(text)

def chunk_tokens(tokens: List[int], chunk_size: int) -> List[List[int]]:
    return [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]

# API Endpoints
@app.post("/scrape")
async def scrape_urls(request: ScrapeRequest):
    print("Started scraping...")
    visited_urls = set()
    all_text = []
    
    async def crawl(url: str, depth: int):
        if depth < 0 or url in visited_urls:
            return
        
        visited_urls.add(url)
        async with aiohttp.ClientSession() as session:
            html_content = await fetch_url(session, url)
            if html_content:
                text = extract_text(html_content)
                all_text.append(text)
                
                if depth > 0:
                    links = extract_links(html_content, url)
                    tasks = [crawl(link, depth - 1) for link in links]
                    await asyncio.gather(*tasks)
    
    tasks = [crawl(url, request.depth) for url in request.urls]
    await asyncio.gather(*tasks)
    
    combined_text = "\n\n".join(all_text)
    save_state("raw_text.json", {"text": combined_text})
    
    return {"status": "success", "message": f"Scraped {len(visited_urls)} pages", "data": combined_text}

@app.post("/process")
async def process_text(request: ProcessRequest):
    tokens = tokenize_text(request.text)
    chunks = chunk_tokens(tokens, request.chunk_size)
    
    # Save chunks
    save_state("chunks.json", {"chunks": chunks})
    
    return {"status": "success", "chunks_count": len(chunks)}

@app.post("/update_subjects")
async def update_subjects(request: SubjectUpdateRequest):
    current_state = load_state("subjects.json")
    
    # Use Lollms to process the chunk and update subjects
    # This is a placeholder for the actual LLM integration
    # You would call your LLM here with the appropriate prompt
    
    # For now, we'll just store the chunks and subjects
    if "processed_chunks" not in current_state:
        current_state["processed_chunks"] = []
    current_state["processed_chunks"].append(request.chunk)
    current_state["current_subjects"] = request.current_subjects
    
    save_state("subjects.json", current_state)
    
    return {"status": "success", "current_subjects": request.current_subjects}

@app.get("/status")
async def get_status():
    try:
        raw_text = load_state("raw_text.json")
        chunks = load_state("chunks.json")
        subjects = load_state("subjects.json")
        
        return {
            "has_raw_text": bool(raw_text),
            "chunks_count": len(chunks.get("chunks", [])),
            "processed_chunks": len(subjects.get("processed_chunks", [])),
            "subjects": subjects.get("current_subjects", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rewrite_subject/{subject}")
async def rewrite_subject(subject: str):
    subjects_data = load_state("subjects.json")
    if subject not in subjects_data.get("current_subjects", []):
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Here you would use Lollms to rewrite the subject content
    # This is a placeholder for the actual LLM integration
    
    return {"status": "success", "subject": subject}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)