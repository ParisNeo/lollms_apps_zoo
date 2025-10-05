"""
AIluminator: Enhanced AI-Generated Text Detection Web App
Author: ParisNeo & Perplexity (Enhanced)
Description:
Advanced FastAPI app with improved detection algorithms for AI vs human text.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import re
import uvicorn
import argparse
from collections import Counter
import math

app = FastAPI(
    title="AIluminator Enhanced",
    description="Advanced detection and highlighting of AI-generated passages in text.",
    version="2.0.0"
)
templates = Jinja2Templates(directory="templates")

# Common AI writing patterns and markers
AI_PHRASES = [
    "it's important to note", "it's worth noting", "keep in mind",
    "delve into", "navigating", "landscape", "robust", "streamline",
    "leverage", "facilitate", "utilize", "aforementioned", "in conclusion",
    "to summarize", "in summary", "moreover", "furthermore", "additionally",
    "it is essential", "crucial to understand", "comprehensive", "multifaceted",
    "cutting-edge", "state-of-the-art", "game-changer", "revolutionize"
]

# Human writing markers
HUMAN_MARKERS = [
    "i think", "i feel", "in my opinion", "personally", "honestly",
    "lol", "lmao", "tbh", "imo", "btw", "omg", "yeah", "nah",
    "kinda", "sorta", "gonna", "wanna", "gotta"
]

def calculate_lexical_diversity(text):
    """Calculate type-token ratio (unique words / total words)"""
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) == 0:
        return 0.5
    return len(set(words)) / len(words)

def calculate_vocabulary_sophistication(text):
    """Measure vocabulary complexity"""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.5
    
    # AI tends to use words of moderate length consistently
    avg_length = sum(len(w) for w in words) / len(words)
    length_variance = sum((len(w) - avg_length) ** 2 for w in words) / len(words)
    
    # Low variance + moderate length = more AI-like
    consistency_score = 1 / (1 + length_variance)
    ideal_ai_length = 5.5
    length_score = 1 - abs(avg_length - ideal_ai_length) / 5
    length_score = max(0, min(1, length_score))
    
    return (consistency_score * 0.5 + length_score * 0.5)

def check_ai_phrases(text):
    """Count AI-typical phrases in text"""
    text_lower = text.lower()
    count = sum(1 for phrase in AI_PHRASES if phrase in text_lower)
    return min(1.0, count * 0.25)

def check_human_markers(text):
    """Count human-typical expressions"""
    text_lower = text.lower()
    count = sum(1 for marker in HUMAN_MARKERS if marker in text_lower)
    return min(1.0, count * 0.3)

def analyze_punctuation_patterns(text):
    """AI tends to use punctuation very consistently"""
    sentences = re.split(r'[.!?]+', text)
    if len(sentences) < 2:
        return 0.5
    
    # Count commas per sentence
    comma_counts = [s.count(',') for s in sentences if s.strip()]
    if not comma_counts:
        return 0.5
    
    avg_commas = sum(comma_counts) / len(comma_counts)
    variance = sum((c - avg_commas) ** 2 for c in comma_counts) / len(comma_counts)
    
    # Low variance = more consistent = more AI-like
    consistency = 1 / (1 + variance)
    return consistency

def analyze_sentence_complexity(text):
    """Analyze complexity and structure"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return 0.5
    
    lengths = [len(s.split()) for s in sentences]
    avg_length = sum(lengths) / len(lengths)
    
    # AI prefers moderate sentence length (15-25 words)
    if 15 <= avg_length <= 25:
        return 0.8
    elif 10 <= avg_length <= 30:
        return 0.6
    else:
        return 0.4

def detect_code_patterns(text):
    """Detect if text contains code, which has different characteristics"""
    code_indicators = [
        r'def\s+\w+\s*\(',  # Python functions
        r'class\s+\w+',     # Class definitions
        r'import\s+\w+',    # Import statements
        r'from\s+\w+\s+import',
        r'return\s+\w+',
        r'if\s+\w+\s*[=<>!]',
        r'for\s+\w+\s+in\s+',
        r'while\s+\w+',
        r'\bprint\s*\(',
        r'#.*$',  # Comments
    ]
    
    matches = sum(1 for pattern in code_indicators if re.search(pattern, text, re.MULTILINE))
    return matches > 2

def detect_ai_passages(text):
    """
    Enhanced passage-based detection algorithm.
    Splits text into passages (2-4 sentences) and analyzes each.
    Returns: (overall_ai_likelihood, highlights:list)
    """
    # Check if it's code
    if detect_code_patterns(text):
        # Code is usually written by humans or is a mix
        # We'll analyze it differently
        is_code = True
    else:
        is_code = False
    
    # Split into sentences first
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if len(s.strip()) > 10]
    
    if not sentences:
        return 0.5, []
    
    # Group sentences into passages (2-4 sentences each)
    passages = []
    i = 0
    while i < len(sentences):
        passage_size = min(3, len(sentences) - i)  # 1-3 sentences per passage
        passage_text = ' '.join(sentences[i:i+passage_size])
        passages.append(passage_text)
        i += passage_size
    
    highlights = []
    
    for passage in passages:
        words = re.findall(r'\b\w+\b', passage)
        if len(words) < 5:
            continue
        
        # Factor 1: Lexical diversity
        lex_diversity = calculate_lexical_diversity(passage)
        diversity_score = 1 - lex_diversity  # Lower diversity = more AI
        
        # Factor 2: Vocabulary sophistication/consistency
        vocab_score = calculate_vocabulary_sophistication(passage)
        
        # Factor 3: AI phrases
        ai_phrase_score = check_ai_phrases(passage)
        
        # Factor 4: Human markers (reduces AI score)
        human_marker_score = check_human_markers(passage)
        
        # Factor 5: Punctuation patterns
        punctuation_score = analyze_punctuation_patterns(passage)
        
        # Factor 6: Sentence complexity
        complexity_score = analyze_sentence_complexity(passage)
        
        # Factor 7: Repetition analysis
        word_counts = Counter(words)
        total_words = len(words)
        repeated_words = sum(count for count in word_counts.values() if count > 1)
        repetition_ratio = repeated_words / total_words if total_words > 0 else 0
        
        # Factor 8: Check for very formal/technical vocabulary
        formal_words = ['utilize', 'facilitate', 'implement', 'demonstrate', 
                       'comprehensive', 'significant', 'substantial', 'optimal',
                       'paramount', 'crucial', 'essential', 'fundamental']
        formal_count = sum(1 for word in words if word.lower() in formal_words)
        formality_score = min(1.0, formal_count / max(1, len(words) / 10))
        
        if is_code:
            # For code, adjust weights
            ai_score = (
                diversity_score * 0.15 +
                vocab_score * 0.15 +
                ai_phrase_score * 0.15 +
                punctuation_score * 0.15 +
                complexity_score * 0.10 +
                repetition_ratio * 0.15 +
                formality_score * 0.15 -
                human_marker_score * 0.30
            )
            # Code is usually less AI-like, so reduce baseline
            ai_score = ai_score * 0.7
        else:
            # Standard text weights
            ai_score = (
                diversity_score * 0.18 +
                vocab_score * 0.16 +
                ai_phrase_score * 0.20 +
                punctuation_score * 0.12 +
                complexity_score * 0.12 +
                repetition_ratio * 0.10 +
                formality_score * 0.12 -
                human_marker_score * 0.25
            )
        
        # Clamp between 0 and 1
        ai_score = max(0, min(1, ai_score))
        
        # Determine suspicion level and classification
        if ai_score >= 0.7:
            suspicion = "high_ai"
            likely = "AI"
        elif ai_score >= 0.55:
            suspicion = "medium_ai"
            likely = "AI"
        elif ai_score >= 0.45:
            suspicion = "neutral"
            likely = "Mixed"
        elif ai_score >= 0.3:
            suspicion = "medium_human"
            likely = "Human"
        else:
            suspicion = "high_human"
            likely = "Human"
        
        highlights.append({
            "text": passage,
            "ai_score": round(ai_score, 3),
            "human_score": round(1 - ai_score, 3),
            "likely": likely,
            "suspicion": suspicion
        })
    
    if not highlights:
        return 0.5, []
    
    overall_ai_likelihood = sum(h["ai_score"] for h in highlights) / len(highlights)
    return overall_ai_likelihood, highlights

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Renders the AIluminator homepage with text input form."""
    return templates.TemplateResponse("index.html", {"request": request, "result": None})

@app.post("/", response_class=HTMLResponse)
async def detect(request: Request, text: str = Form(...)):
    """Receives submitted text, analyzes passages, and returns scored highlights."""
    score, passages = detect_ai_passages(text)
    
    # Calculate statistics
    ai_count = sum(1 for p in passages if p["likely"] == "AI")
    human_count = sum(1 for p in passages if p["likely"] == "Human")
    mixed_count = len(passages) - ai_count - human_count
    
    return templates.TemplateResponse(
        "index.html", {
            "request": request,
            "result": {
                "ai_likelihood": score,
                "passages": passages,
                "ai_count": ai_count,
                "human_count": human_count,
                "mixed_count": mixed_count,
                "total_passages": len(passages)
            },
            "text": text
        }
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AIluminator Enhanced FastAPI server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()
    uvicorn.run("server:app", host=args.host, port=args.port, reload=True)