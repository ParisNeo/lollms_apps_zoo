import sqlite3
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import datetime
import os
import uvicorn
import threading
import time
import webbrowser
import socket

DATABASE_URL = "./adhd_app.db"
HOST = "127.0.0.1"
PORT = 8000
INDEX_HTML_PATH = "index.html"
SERVER_ROOT_URL = f"http://{HOST}:{PORT}/"

# --- Database Setup ---
def init_db():
    # ... (your init_db code is fine) ...
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'todo',
        pomodoros_completed INTEGER DEFAULT 0,
        pomodoros_estimated INTEGER DEFAULT 1,
        points_value INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        total_points INTEGER DEFAULT 0
    )
    """)
    cursor.execute("INSERT OR IGNORE INTO user_stats (id, total_points) VALUES (1, 0)")
    try:
        cursor.execute("SELECT points_value FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE tasks ADD COLUMN points_value INTEGER DEFAULT 10")
    conn.commit()
    conn.close()


# --- Pydantic Models ---
# ... (your Pydantic models are fine) ...
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = 'todo'
    pomodoros_estimated: Optional[int] = Field(default=1, ge=0)
    points_value: Optional[int] = Field(default=10, ge=0)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    pomodoros_estimated: Optional[int] = Field(default=None, ge=0)
    pomodoros_completed: Optional[int] = Field(default=None, ge=0)
    points_value: Optional[int] = Field(default=None, ge=0)

class TaskResponse(TaskBase):
    id: int
    pomodoros_completed: int
    created_at: str
    updated_at: str

class UserStatsResponse(BaseModel):
    total_points: int

# --- FastAPI App Instance ---
app = FastAPI(title="ADHD Focus Hub API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper to get DB connection ---
# ... (your DB helpers are fine) ...
def get_db():
    db = sqlite3.connect(DATABASE_URL)
    db.row_factory = sqlite3.Row
    return db

def update_user_points(db: sqlite3.Connection, points_to_add: int):
    cursor = db.cursor()
    cursor.execute("UPDATE user_stats SET total_points = total_points + ? WHERE id = 1", (points_to_add,))
    db.commit()


# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def serve_index_html():
    index_path = os.path.join(os.path.dirname(__file__), INDEX_HTML_PATH)
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail=f"{INDEX_HTML_PATH} not found at {index_path}")
    return FileResponse(index_path)

# ... (your /tasks, /stats, etc. API endpoints are fine) ...
@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    db = get_db()
    cursor = db.cursor()
    now = datetime.datetime.now().isoformat()
    try:
        cursor.execute(
            """
            INSERT INTO tasks (title, description, due_date, status, pomodoros_estimated, points_value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (task.title, task.description, task.due_date, task.status, task.pomodoros_estimated, task.points_value, now, now)
        )
        db.commit()
        task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        created_task_row = cursor.fetchone()
        if not created_task_row:
             raise HTTPException(status_code=500, detail="Failed to retrieve created task")
        return dict(created_task_row)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        db.close()

@app.get("/tasks", response_model=List[TaskResponse])
async def read_tasks():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
    tasks = [dict(row) for row in cursor.fetchall()]
    db.close()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def read_task(task_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    db.close()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return dict(task)

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT status, points_value FROM tasks WHERE id = ?", (task_id,))
    current_task_data = cursor.fetchone()
    if not current_task_data:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    current_status = current_task_data["status"]
    points_for_this_task = current_task_data["points_value"]
    fields_to_update = task_update.model_dump(exclude_unset=True)
    if not fields_to_update:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    fields_to_update["updated_at"] = datetime.datetime.now().isoformat()
    set_clause = ", ".join([f"{key} = ?" for key in fields_to_update.keys()])
    values = list(fields_to_update.values())
    values.append(task_id)

    try:
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", tuple(values))
        if task_update.status == 'done' and current_status != 'done':
            update_user_points(db, points_for_this_task)
        db.commit()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_task_row = cursor.fetchone()
        if not updated_task_row:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated task")
        return dict(updated_task_row)
    except sqlite3.Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during update: {e}")
    finally:
        db.close()

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if cursor.rowcount == 0:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.close()
    return None

@app.post("/tasks/{task_id}/complete_pomodoro", response_model=TaskResponse)
async def complete_pomodoro_for_task(task_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT pomodoros_completed, pomodoros_estimated, status, points_value FROM tasks WHERE id = ?", (task_id,))
    task_data = cursor.fetchone()
    if not task_data:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task_data["status"] == 'done':
        db.close()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return dict(cursor.fetchone())

    new_pomodoros_completed = task_data["pomodoros_completed"] + 1
    points_for_pomodoro = 1
    update_user_points(db, points_for_pomodoro)
    new_status = task_data["status"]
    if new_pomodoros_completed >= task_data["pomodoros_estimated"] and task_data["status"] != 'done':
        new_status = 'done'
        if task_data["status"] != 'done':
             update_user_points(db, task_data["points_value"])

    cursor.execute(
        "UPDATE tasks SET pomodoros_completed = ?, status = ?, updated_at = ? WHERE id = ?",
        (new_pomodoros_completed, new_status, datetime.datetime.now().isoformat(), task_id)
    )
    db.commit()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_task = cursor.fetchone()
    db.close()
    return dict(updated_task)

@app.get("/stats", response_model=UserStatsResponse)
async def get_user_stats():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT total_points FROM user_stats WHERE id = 1")
    stats = cursor.fetchone()
    db.close()
    if not stats:
        return UserStatsResponse(total_points=0)
    return UserStatsResponse(total_points=stats["total_points"])


# --- Server Start and Browser Opening Logic ---
def run_server():
    """Runs the Uvicorn server programmatically."""
    print("Starting Uvicorn server programmatically (reload disabled in this mode).")
    print(f"Access the application at {SERVER_ROOT_URL}")
    # When running in a thread, it's safer to disable reload or use uvicorn.Server
    # reload=True often causes issues with signal handling in threads.
    # For development with reload, run: uvicorn server:app --reload
    config = uvicorn.Config("server:app", host=HOST, port=PORT, log_level="info", workers=1)
    server = uvicorn.Server(config)
    server.run() # This call blocks within this thread.

def check_server_ready(host, port, retries=15, delay=1):
    # ... (check_server_ready function is fine) ...
    for i in range(retries):
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"Server on {host}:{port} is ready.")
                return True
        except (socket.error, ConnectionRefusedError):
            if i < retries - 1:
                 print(f"Server not ready yet (attempt {i+1}/{retries}). Retrying in {delay}s...")
            time.sleep(delay)
    print(f"Server on {host}:{port} did not become ready after {retries} attempts.")
    return False

if __name__ == "__main__":
    print(f"Looking for database at: {os.path.abspath(DATABASE_URL)}")
    if not os.path.exists(DATABASE_URL) or os.path.getsize(DATABASE_URL) == 0:
        print(f"Database not found or empty, initializing at {DATABASE_URL}...")
        init_db()
    else:
        print(f"Using existing database: {DATABASE_URL}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    # print(f"FastAPI server starting in a background thread on {SERVER_ROOT_URL}") # Moved into run_server

    if check_server_ready(HOST, PORT):
        print(f"Opening application in browser at: {SERVER_ROOT_URL}")
        webbrowser.open_new_tab(SERVER_ROOT_URL)
    else:
        print(f"Could not confirm server readiness. Please open {SERVER_ROOT_URL} manually if the server starts.")

    try:
        # Keep the main thread alive to allow the daemon server_thread to run
        # and to catch KeyboardInterrupt for a cleaner shutdown.
        while server_thread.is_alive():
            server_thread.join(timeout=0.5) # Check periodically
    except KeyboardInterrupt:
        print("\nCtrl+C received in main thread. Uvicorn should shut down gracefully.")
        # Uvicorn, when started with server.run(), should handle SIGINT properly.
        # The daemon thread will exit once server.run() returns or the main thread exits.
    finally:
        print("Main script process finished.")
