import os
import uuid
import subprocess
from typing import Optional

from fastapi import FastAPI, Request, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'flv'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB limit for uploads

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# --- Helper Functions ---

def allowed_file(filename: str) -> bool:
    """Checks if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_dir(directory: str) -> None:
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_output_filename(original_filename: str, suffix: str = "processed") -> str:
    """Generates a unique output filename."""
    base, ext = os.path.splitext(original_filename)
    unique_id = uuid.uuid4().hex[:8]
    return f"{base}_{suffix}_{unique_id}.mp4"  # Always output as mp4

# --- FastAPI Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request, "error": None})


@app.post("/process", response_class=HTMLResponse)
async def process_video(
    request: Request,
    video: UploadFile,
    compress: Optional[str] = Form(None),  # "on" if checked, None otherwise
    resolution: str = Form("original"),
    crop: str = Form("none")
):
    """Handles video upload and initiates FFmpeg processing."""
    if not video:
        return templates.TemplateResponse("index.html", {"request": request, "error": "No video file selected."})

    filename = video.filename
    if not filename:
        return templates.TemplateResponse("index.html", {"request": request, "error": "No video file selected."})

    if not allowed_file(filename):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Invalid file type. Allowed: " + ", ".join(ALLOWED_EXTENSIONS)},
        )

    # --- Prepare File Paths ---
    ensure_dir(UPLOAD_FOLDER)
    ensure_dir(PROCESSED_FOLDER)

    original_filename = secure_filename(filename)
    upload_path = os.path.join(UPLOAD_FOLDER, original_filename)
    output_filename = get_output_filename(original_filename)
    output_path = os.path.join(PROCESSED_FOLDER, output_filename)

    try:
        # Save the uploaded file
        contents = await video.read()  # Read the file contents
        with open(upload_path, "wb") as f:
            f.write(contents)

    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": f"Error saving uploaded file: {e}"}
        )


    # --- Build FFmpeg Command ---
    cmd = ['ffmpeg', '-i', upload_path]

    # Video Filters (vf) - build dynamically
    vf_options = []

    # 1. Cropping (applied first if needed)
    if crop == '16:9':
        vf_options.append('crop=min(iw\\,ih*16/9):min(ih\\,iw*9/16)')
    elif crop == '9:16':
        vf_options.append('crop=min(iw\\,ih*9/16):min(ih\\,iw*16/9)')
    elif crop == '1:1':
        vf_options.append('crop=min(iw\\,ih):min(iw\\,ih)')
    elif crop == '4:3':
        vf_options.append('crop=min(iw\\,ih*4/3):min(ih\\,iw*3/4)')

    # 2. Resolution/Scaling (applied after crop if any)
    scale_option = None
    if resolution == '1080p':
        scale_option = 'scale=-2:1080'  # -2 maintains aspect ratio
    elif resolution == '720p':
        scale_option = 'scale=-2:720'
    elif resolution == '480p':
        scale_option = 'scale=-2:480'
    elif resolution == '360p':
        scale_option = 'scale=-2:360'

    if scale_option:
        vf_options.append(scale_option)

    # Apply video filters if any were added
    if vf_options:
        cmd.extend(['-vf', ','.join(vf_options)])

    # 3. Compression (applied last)
    if compress == 'on':  # Check if checkbox was checked
        cmd.extend(['-c:v', 'libx264', '-crf', '28', '-preset', 'medium'])
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
    else:
        if vf_options:
            cmd.extend(['-c:v', 'libx264', '-preset', 'medium'])
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])  # Decent audio quality
        else:
            cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])

    # Output file path
    cmd.append(output_path)

    # --- Execute FFmpeg ---
    print(f"Running FFmpeg command: {' '.join(cmd)}")
    try:
        process = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        print("FFmpeg stdout:", process.stdout)
        print("FFmpeg stderr:", process.stderr)

        try:
            os.remove(upload_path)
        except OSError as e:
            print(f"Error removing uploaded file {upload_path}: {e}")

        return templates.TemplateResponse(
            "download.html", {"request": request, "filename": output_filename}
        )

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg failed with exit code {e.returncode}")
        print("FFmpeg stdout:", e.stdout)
        print("FFmpeg stderr:", e.stderr)
        error_message = f"Error during video processing: FFmpeg failed. Check server logs. Error: {e.stderr[:200]}..."
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return templates.TemplateResponse("index.html", {"request": request, "error": error_message})

    except subprocess.TimeoutExpired:
        print("FFmpeg command timed out.")
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": "Video processing took too long and was stopped."}
        )

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(upload_path):
            os.remove(upload_path)
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": f"An unexpected error occurred: {e}"}
        )


@app.get("/downloads/{filename}")
async def download_file(filename: str):
    """Provides the processed file for download."""
    safe_filename = secure_filename(filename)
    file_path = os.path.join(PROCESSED_FOLDER, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=safe_filename, media_type="video/mp4")

# --- Main Execution ---

if __name__ == '__main__':
    import uvicorn

    ensure_dir(UPLOAD_FOLDER)
    ensure_dir(PROCESSED_FOLDER)
    uvicorn.run(app, host="0.0.0.0", port=8000)