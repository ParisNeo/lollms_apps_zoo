# Import necessary libraries
import os

import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pdf2docx import Converter

app = FastAPI()

# Allow CORS for localhost:9600
origins = [
    "http://localhost:9600",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/convert_pdf2docx")
async def convert_pdf_to_docx(file: UploadFile = File(...)):
    # Save the uploaded PDF file
    pdf_file_path = f"temp_{file.filename}"
    with open(pdf_file_path, "wb") as pdf_file:
        pdf_file.write(await file.read())

    # Convert PDF to DOCX
    docx_file_path = pdf_file_path.replace(".pdf", ".docx")
    cv = Converter(pdf_file_path)
    cv.convert(docx_file_path, start=0, end=None)
    cv.close()

    # Remove the PDF file after conversion
    os.remove(pdf_file_path)

    # Return the DOCX file
    return FileResponse(
        docx_file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(docx_file_path),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
