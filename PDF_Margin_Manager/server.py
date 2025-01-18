from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Form
from fastapi.responses import FileResponse
from PyPDF2 import PdfReader, PdfWriter, Transformation
from pydantic import BaseModel
from PyPDF2 import PdfReader, PdfWriter, Transformation
from PyPDF2.generic import FloatObject, RectangleObject

import tempfile
import os
from typing import Optional
from pydantic import BaseModel
import io
import json
import logging

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Set up logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the MarginSettings model at module level
class MarginSettings(BaseModel):
    top: float
    bottom: float
    left: float
    right: float

    class Config:
        validate_assignment = True

def process_pdf(content: bytes, margins: MarginSettings) -> str:
    """
    Process the PDF with the given margins.
    Returns the path to the processed PDF file.
    """
    pdf_reader = PdfReader(io.BytesIO(content))
    pdf_writer = PdfWriter()
    
    for page_num, page in enumerate(pdf_reader.pages):
        # Get original dimensions
        original_width = float(page.mediabox.width)
        original_height = float(page.mediabox.height)
        
        # Calculate new dimensions
        new_width = original_width + margins.left + margins.right
        new_height = original_height + margins.top + margins.bottom
        
        # Create a new page with modified dimensions
        # Move the content by adjusting the mediabox and cropbox
        page.mediabox.left = -margins.left
        page.mediabox.bottom = -margins.bottom
        page.mediabox.right = original_width + margins.right
        page.mediabox.top = original_height + margins.top
        
        if hasattr(page, 'cropbox'):
            page.cropbox.left = -margins.left
            page.cropbox.bottom = -margins.bottom
            page.cropbox.right = original_width + margins.right
            page.cropbox.top = original_height + margins.top
            
        pdf_writer.add_page(page)
    
    # Save to temporary file
    tmp_path = tempfile.mktemp(suffix='.pdf')
    with open(tmp_path, 'wb') as tmp:
        pdf_writer.write(tmp)
    
    return tmp_path



@app.post("/api/add-margins")
async def add_margins(
    file: UploadFile = File(...),
    margins: str = Form(...),
):
    """
    Add margins to a PDF file.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF"
            )

        # Parse and validate margins
        logger.info(f"Received margins: {margins}")
        try:
            margins_dict = json.loads(margins)
            margins_settings = MarginSettings(**margins_dict)
            logger.info(f"Parsed margins settings: {margins_settings}")
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON format for margins: {str(e)}"
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid margins values: {str(e)}"
            )

        # Read file content
        content = await file.read()
        logger.info(f"Read file content, size: {len(content)} bytes")

        # Process the PDF
        tmp_path = process_pdf(content, margins_settings)
        logger.info(f"PDF processed and saved to: {tmp_path}")

        # Return the processed file
        return FileResponse(
            tmp_path,
            media_type='application/pdf',
            filename=f"processed_{file.filename}",
            background=None
        )

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)