import os
import subprocess
import tempfile

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

# Allow CORS for frontend requests from localhost:9600
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9600"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExportPDFRequest(BaseModel):
    latex: str
    assets: dict


@app.post("/export-pdf")
async def export_pdf(request: ExportPDFRequest):
    latex = request.latex
    assets = request.assets
    # Create a temporary directory to store the LaTeX files and assets
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write the LaTeX code to a .tex file
        tex_file_path = os.path.join(temp_dir, "document.tex")
        with open(tex_file_path, "w") as tex_file:
            tex_file.write(latex)

        # Save assets (images, etc.) to the temporary directory
        for filename, data in assets.items():
            asset_path = os.path.join(temp_dir, filename)
            with open(asset_path, "wb") as asset_file:
                asset_file.write(data)

        # Compile the LaTeX document to PDF
        try:
            subprocess.run(
                ["pdflatex", "-output-directory", temp_dir, tex_file_path], check=True
            )
            pdf_file_path = os.path.join(temp_dir, "document.pdf")
            return FileResponse(
                pdf_file_path,
                media_type="application/pdf",
                filename="latex_document.pdf",
            )
        except subprocess.CalledProcessError:
            return {"error": "Failed to compile LaTeX document."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
