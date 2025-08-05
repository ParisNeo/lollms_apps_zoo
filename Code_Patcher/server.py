# lollms-code-patcher/app.py
import uvicorn
import argparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import patch as patch_lib

class PatchRequest(BaseModel):
    original_code: str
    patch_text: str

app = FastAPI(
    title="Code Patcher API",
    description="An API to apply git-style patches to code.",
    version="1.0.0"
)

def normalize_text(text: str) -> str:
    """Converts all line endings to LF and ensures a single trailing newline."""
    # Convert CRLF to LF
    text = text.replace('\r\n', '\n')
    # Strip all trailing whitespace (including newlines)
    text = text.rstrip()
    # Add a single trailing newline
    return text + '\n'

@app.post("/patch")
async def apply_patch(request: PatchRequest):
    """
    Receives original code and a patch, applies the patch, and returns the new code.
    """
    try:
        # --- DEFINITIVE FIX: Normalize both inputs to have a trailing newline ---
        original_code_normalized = normalize_text(request.original_code)
        patch_text_normalized = normalize_text(request.patch_text)

        patch_set = patch_lib.fromstring(patch_text_normalized.encode('utf-8'))
        
        if not patch_set:
            raise ValueError("Invalid patch format. The provided patch text could not be parsed.")

        patched_code_bytes = patch_set.apply(original_code_normalized.encode('utf-8'))

        if patched_code_bytes is False:
            raise ValueError("Patch could not be applied. It may not match the original code or may have already been applied.")

        # Decode and strip the trailing newline for a clean output in the editor
        patched_code = patched_code_bytes.decode('utf-8').rstrip()
        return JSONResponse(content={"patched_code": patched_code})
    
    except Exception as e:
        print(f"Error applying patch: {e}")
        raise HTTPException(status_code=400, detail=str(e))

app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Code Patcher Lollms App")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=9601, help="Port to run the server on")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)