import uvicorn
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import time, date

DB_FILE = Path("database.json")

def load_db() -> Dict[str, Any]:
    if not DB_FILE.exists():
        return {}
    with DB_FILE.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_db(data: Dict[str, Any]):
    with DB_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)

app = FastAPI(
    title="API de Simulation pour Assistante Maternelle",
    description="Une API complète pour gérer les simulations de paie d'assistantes maternelles.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HeuresJournalieres(BaseModel):
    debut: Optional[time] = None
    fin: Optional[time] = None

class PlanningHebdomadaire(BaseModel):
    lundi: Optional[HeuresJournalieres] = None
    mardi: Optional[HeuresJournalieres] = None
    mercredi: Optional[HeuresJournalieres] = None
    jeudi: Optional[HeuresJournalieres] = None
    vendredi: Optional[HeuresJournalieres] = None
    samedi: Optional[HeuresJournalieres] = None

class SimulationInput(BaseModel):
    planning: PlanningHebdomadaire
    tarif_horaire_net: float = Field(..., gt=0)
    frais_entretien_par_jour: float = Field(default=3.73, ge=0)
    type_contrat: str = Field(..., pattern="^(annee_complete|annee_incomplete)$")
    semaines_travaillees_par_an: Optional[int] = Field(None, ge=1, le=46)
    date_debut_contrat: date

class SessionData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    config: SimulationInput

class SessionListItem(BaseModel):
    id: str
    name: str

@app.get("/api/sessions", response_model=List[SessionListItem])
def get_sessions_list():
    db = load_db()
    return [{"id": session_id, "name": session_data.get("name", "Sans nom")} for session_id, session_data in db.items()]

@app.post("/api/sessions", response_model=SessionData, status_code=201)
def create_session(session_data: SessionData = Body(...)):
    db = load_db()
    if not session_data.id:
        session_data.id = str(uuid.uuid4())
    db[session_data.id] = session_data.dict()
    save_db(db)
    return session_data

@app.get("/api/sessions/{session_id}", response_model=SessionData)
def get_session_details(session_id: str):
    db = load_db()
    session = db.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.put("/api/sessions/{session_id}", response_model=SessionData)
def update_session(session_id: str, session_data: SessionData = Body(...)):
    db = load_db()
    if session_id not in db:
        raise HTTPException(status_code=404, detail="Session not found")
    session_data.id = session_id
    db[session_id] = session_data.dict()
    save_db(db)
    return session_data

@app.delete("/api/sessions/{session_id}", status_code=204)
def delete_session(session_id: str):
    db = load_db()
    if session_id not in db:
        raise HTTPException(status_code=404, detail="Session not found")
    del db[session_id]
    save_db(db)

@app.post("/api/sessions/{session_id}/duplicate", response_model=SessionData, status_code=201)
def duplicate_session(session_id: str):
    db = load_db()
    original_session_data = db.get(session_id)
    if not original_session_data:
        raise HTTPException(status_code=404, detail="Session à dupliquer non trouvée")

    new_session = SessionData.parse_obj(original_session_data)
    new_session.id = str(uuid.uuid4())
    new_session.name = f"{new_session.name} (Copie)"
    
    db[new_session.id] = new_session.dict()
    save_db(db)
    return new_session

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)