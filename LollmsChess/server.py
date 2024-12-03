from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
from lollms_client import LOLLMSClient

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChessMove(BaseModel):
    board_state: str
    last_move: Optional[str] = None

class ChessResponse(BaseModel):
    move: str
    explanation: str

# Initialize LOLLMS client
lollms_client = LOLLMSClient()

CHESS_MOVE_PROMPT = """You are playing as a chess AI. Given the current board state in FEN notation and the last move played, provide your next move.
The board state is: {board_state}
Last move played: {last_move}

Respond strictly in the following JSON format:
{
    "move": "e2e4",  # Your move in algebraic notation (from square to square)
    "explanation": "I chose this move because..." # Brief explanation of your strategic thinking
}

Make sure your move is legal and follows chess rules. Analyze the position carefully and make a strong strategic move."""

@app.post("/api/make_move")
async def make_move(move_data: ChessMove):
    try:
        # Format the prompt with the current game state
        prompt = CHESS_MOVE_PROMPT.format(
            board_state=move_data.board_state,
            last_move=move_data.last_move if move_data.last_move else "Game start"
        )
        
        # Generate response using LOLLMS
        response = await lollms_client.generateCode(prompt)
        
        if not response:
            raise HTTPException(status_code=500, detail="Failed to generate move")
            
        # Parse the response JSON
        try:
            move_json = json.loads(response)
            return ChessResponse(
                move=move_json["move"],
                explanation=move_json["explanation"]
            )
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from AI")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)