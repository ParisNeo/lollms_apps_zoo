import sqlite3
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import datetime
import os

DATABASE_URL = "./adhd_app.db"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    # Tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'todo',  -- 'todo', 'doing', 'done'
        pomodoros_completed INTEGER DEFAULT 0,
        pomodoros_estimated INTEGER DEFAULT 1,
        points_value INTEGER DEFAULT 10, -- Points awarded when task is marked done
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # User Stats (simple version, one row for the single user)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY CHECK (id = 1), -- Ensure only one row
        total_points INTEGER DEFAULT 0
    )
    """)
    # Initialize user_stats if empty
    cursor.execute("INSERT OR IGNORE INTO user_stats (id, total_points) VALUES (1, 0)")
    
    # Add points_value column if it doesn't exist (for migration)
    try:
        cursor.execute("SELECT points_value FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding points_value column to tasks table...")
        cursor.execute("ALTER TABLE tasks ADD COLUMN points_value INTEGER DEFAULT 10")

    conn.commit()
    conn.close()

# --- Pydantic Models ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None # Store as ISO date string e.g., "YYYY-MM-DD"
    status: Optional[str] = 'todo'
    pomodoros_estimated: Optional[int] = Field(default=1, ge=0)
    points_value: Optional[int] = Field(default=10, ge=0)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel): # More flexible updates
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    pomodoros_estimated: Optional[int] = Field(default=None, ge=0)
    pomodoros_completed: Optional[int] = Field(default=None, ge=0) # Allow direct update if needed
    points_value: Optional[int] = Field(default=None, ge=0)


class TaskResponse(TaskBase):
    id: int
    pomodoros_completed: int
    created_at: str # Store as ISO string
    updated_at: str # Store as ISO string

class UserStatsResponse(BaseModel):
    total_points: int

# --- FastAPI App Instance ---
app = FastAPI(title="ADHD Focus Hub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper to get DB connection ---
def get_db():
    db = sqlite3.connect(DATABASE_URL)
    db.row_factory = sqlite3.Row # Access columns by name
    return db

# --- Utility Functions ---
def update_user_points(db: sqlite3.Connection, points_to_add: int):
    cursor = db.cursor()
    cursor.execute("UPDATE user_stats SET total_points = total_points + ? WHERE id = 1", (points_to_add,))
    db.commit()

# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    init_db()

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
        
        # Fetch the created task to return it
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
    
    # Fetch current task to see if it's being marked 'done'
    cursor.execute("SELECT status, points_value FROM tasks WHERE id = ?", (task_id,))
    current_task_data = cursor.fetchone()
    if not current_task_data:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    current_status = current_task_data["status"]
    points_for_this_task = current_task_data["points_value"]

    fields_to_update = task_update.model_dump(exclude_unset=True) # Get only provided fields
    if not fields_to_update:
        db.close()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    fields_to_update["updated_at"] = datetime.datetime.now().isoformat()
    
    set_clause = ", ".join([f"{key} = ?" for key in fields_to_update.keys()])
    values = list(fields_to_update.values())
    values.append(task_id)

    try:
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", tuple(values))
        
        # Gamification: Award points if task is newly marked as 'done'
        if task_update.status == 'done' and current_status != 'done':
            update_user_points(db, points_for_this_task)

        db.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_task_row = cursor.fetchone()
        if not updated_task_row: # Should not happen if update was successful
            raise HTTPException(status_code=500, detail="Failed to retrieve updated task")
        
        return dict(updated_task_row)

    except sqlite3.Error as e:
        db.rollback() # Rollback on error
        raise HTTPException(status_code=500, detail=f"Database error during update: {e}")
    finally:
        db.close()


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    db = get_db()
    cursor = db.cursor()
    # Optional: If deleting a 'done' task should subtract points (usually not desired)
    # cursor.execute("SELECT status, points_value FROM tasks WHERE id = ?", (task_id,))
    # task_data = cursor.fetchone()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    if cursor.rowcount == 0:
        db.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # if task_data and task_data['status'] == 'done':
    #     update_user_points(db, -task_data['points_value']) # Subtract points

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
        db.close() # No changes if already done
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) # Fetch and return current state
        return dict(cursor.fetchone())


    new_pomodoros_completed = task_data["pomodoros_completed"] + 1
    
    # Basic gamification: 1 point per Pomodoro
    points_for_pomodoro = 1 
    update_user_points(db, points_for_pomodoro)

    new_status = task_data["status"]
    # If pomodoros completed meet estimated, mark as done
    # (This is also handled on frontend, but good to have backend logic too)
    if new_pomodoros_completed >= task_data["pomodoros_estimated"] and task_data["status"] != 'done':
        new_status = 'done'
        # Award task completion points only if not already awarded
        # (This check is crucial to avoid double-counting if status is also updated via PUT /tasks/{id})
        if task_data["status"] != 'done': # Check original status
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
    if not stats: # Should be initialized, but as a fallback
        return UserStatsResponse(total_points=0)
    return UserStatsResponse(total_points=stats["total_points"])


# To run the server: uvicorn server:app --reload
if __name__ == "__main__":
    import uvicorn
    # Create DB file if it doesn't exist in the current directory
    if not os.path.exists(DATABASE_URL):
        print(f"Database not found at {DATABASE_URL}, initializing...")
        init_db()
    elif os.path.getsize(DATABASE_URL) == 0: # If file exists but is empty
        print(f"Database file at {DATABASE_URL} is empty, initializing...")
        init_db()
    else:
        print(f"Using existing database: {DATABASE_URL}")

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
