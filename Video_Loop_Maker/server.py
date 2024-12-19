import os
import subprocess
import sys
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


def ensure_ffmpeg_installed():
    try:
        print("Checking FFmpeg installation.")
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("FFmpeg is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg not found. Attempting to install...")
        import ffmpeg_installer

        if ffmpeg_installer.install_ffmpeg_if_needed():
            print("FFmpeg installation completed.")
        else:
            print(
                "FFmpeg installation failed or requires restart. Please run the script again."
            )
            sys.exit(1)


ensure_ffmpeg_installed()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure temporary directory exists
os.makedirs("temp", exist_ok=True)


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    # Generate a unique filename
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_location = f"temp/{filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    return {"filename": filename}


@app.post("/create_loop")
async def create_loop(filename: str = Form(...)):
    input_path = f"temp/{filename}"
    if not os.path.exists(input_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    output_path = f"temp/looped_{filename}"

    # FFmpeg command to create a loop
    cmd = [
        "ffmpeg",
        "-i",
        input_path,
        "-filter_complex",
        "[0:v]reverse[r];[0:v][r]concat=n=2:v=1[v]",
        "-map",
        "[v]",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"FFmpeg error: {e.stderr.decode()}"
        )

    return {"looped_filename": f"looped_{filename}"}


@app.get("/video/{filename}")
async def get_video(filename: str):
    file_path = f"temp/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    return FileResponse(file_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
