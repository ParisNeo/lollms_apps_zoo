# lollms-code-patcher/app.py
import uvicorn
import argparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from flexipatch import RobustPatcher # Changed import from patch_lib to flexipatch

class PatchRequest(BaseModel):
    original_code: str
    patch_text: str

app = FastAPI(
    title="Code Patcher API",
    description="An API to apply git-style patches to code using FlexiPatch.", # Updated description
    version="1.0.0"
)

# The normalize_text function is generally not needed when using FlexiPatch,
# as FlexiPatch is designed to handle various line endings and trailing newlines gracefully.
# However, if you want to ensure consistent output formatting, you can keep it
# for post-processing the patched code or remove it if FlexiPatch's default
# output is sufficient. For this upgrade, I will remove its usage as FlexiPatch
# inherently handles these variations in the input.
# You can remove the function definition if it's no longer used anywhere else.
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
    Receives original code and a patch, applies the patch using FlexiPatch, and returns the new code.
    """
    try:
        # Initialize RobustPatcher
        patcher = RobustPatcher()

        # FlexiPatch is designed to handle variations in line endings and trailing newlines
        # directly from the input. So, explicit normalization before passing to FlexiPatch
        # is typically not required.
        
        # Apply the patch
        # FlexiPatch's apply_patch method returns the patched code as a string
        patched_code = patcher.apply_patch(request.original_code, request.patch_text)

        # The original code stripped the trailing newline for a "clean output in the editor".
        # FlexiPatch usually preserves or normalizes trailing newlines, but keeping .rstrip()
        # ensures consistency with the previous behavior if that's desired for your editor.
        return JSONResponse(content={"patched_code": patched_code.rstrip()})
    
    except ValueError as e: # FlexiPatch raises ValueError for invalid patches or application failures
        print(f"Error applying patch with FlexiPatch: {e}")
        # Raise HTTPException with a 400 status code for client-side errors (e.g., bad patch)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch any other unexpected exceptions
        print(f"An unexpected error occurred during patch application: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected internal server error occurred: {e}")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Code Patcher Lollms App")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=9601, help="Port to run the server on")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)