"""
AIluminator: AI-Generated Text Detection Web App
Author: ParisNeo & Perplexity
Description:
A simple FastAPI app that detects and highlights passages likely written by AI or humans.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import re

app = FastAPI(
    title="AIluminator",
    description="Detect and highlight AI-generated passages in text.",
    version="1.0.0"
)
templates = Jinja2Templates(directory="templates")

def detect_ai_passages(text):
    """
    Heuristic detection algorithm to score the likelihood that each sentence is AI-generated.
    Returns: (overall_ai_likelihood, highlights:list)
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    highlights = []
    for sent in sentences:
        unique_words = len(set(sent.split()))
        avg_word_len = sum(len(w) for w in sent.split()) / max(1, len(sent.split()))
        repetition = any(sent.count(word) > 2 for word in sent.split())
        ai_score = (
            (unique_words < 7) +
            (avg_word_len < 4.5) +
            repetition
        ) / 3
        highlights.append({
            "text": sent,
            "ai_score": ai_score,
            "human_score": 1 - ai_score,
            "likely": "AI" if ai_score > 0.6 else "Human"
        })
    overall_ai_likelihood = sum(h["ai_score"] for h in highlights) / len(highlights)
    return overall_ai_likelihood, highlights

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Renders the AIluminator homepage with text input form.
    """
    return templates.TemplateResponse("index.html", {"request": request, "result": None})

@app.post("/", response_class=HTMLResponse)
async def detect(request: Request, text: str = Form(...)):
    """
    Receives submitted text, analyzes passages, and returns scored highlights on the homepage.
    """
    score, passages = detect_ai_passages(text)
    return templates.TemplateResponse(
        "index.html", {
            "request": request,
            "result": {"ai_likelihood": score, "passages": passages},
            "text": text
        }
    )
