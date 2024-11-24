from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psutil

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

import psutil

@app.get("/get_active_processes")
async def get_active_processes():
    processes = []
    cpu_count = psutil.cpu_count()
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
        try:
            process_info = proc.info
            # Update CPU percent with a longer interval
            cpu_percent = proc.cpu_percent(interval=1.0)
            
            # Normalize CPU percent by the number of cores
            normalized_cpu_percent = min(cpu_percent / cpu_count, 100)
            
            processes.append({
                "pid": process_info['pid'],
                "name": process_info['name'],
                "status": process_info['status'],
                "cpu_percent": normalized_cpu_percent,
                "memory_percent": process_info['memory_percent']
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return {"processes": processes}

@app.post("/stop_process/{pid}")
async def stop_process(pid: int):
    try:
        process = psutil.Process(pid)
        process.terminate()  # Sends SIGTERM
        return {"message": f"Process with PID {pid} has been terminated."}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail=f"Process with PID {pid} not found.")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"Access denied to terminate process with PID {pid}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
