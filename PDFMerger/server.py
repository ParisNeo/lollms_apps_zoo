from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import PyPDF2
import io
from datetime import datetime

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Fusion Tool</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                padding: 40px;
                max-width: 600px;
                width: 100%;
            }
            
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 12px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-bottom: 20px;
            }
            
            .upload-area:hover {
                border-color: #764ba2;
                background: #f8f9ff;
            }
            
            .upload-area.dragover {
                border-color: #764ba2;
                background: #f0f0ff;
            }
            
            .upload-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            
            input[type="file"] {
                display: none;
            }
            
            .file-list {
                margin: 20px 0;
                max-height: 300px;
                overflow-y: auto;
            }
            
            .file-item {
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px 15px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                cursor: move;
            }
            
            .file-item:hover {
                background: #e9ecef;
            }
            
            .file-name {
                flex: 1;
                font-size: 14px;
                color: #333;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                margin-right: 10px;
            }
            
            .file-controls {
                display: flex;
                gap: 5px;
            }
            
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                width: 100%;
                padding: 15px;
                font-size: 16px;
            }
            
            .btn-primary:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-primary:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .btn-small {
                padding: 5px 10px;
                font-size: 12px;
                background: #dc3545;
                color: white;
            }
            
            .btn-small:hover {
                background: #c82333;
            }
            
            .order-controls {
                display: flex;
                gap: 5px;
            }
            
            .btn-order {
                padding: 2px 8px;
                font-size: 12px;
                background: #6c757d;
                color: white;
                border-radius: 4px;
            }
            
            .btn-order:hover {
                background: #5a6268;
            }
            
            .message {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                font-size: 14px;
            }
            
            .message.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .message.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .hidden {
                display: none;
            }
            
            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255,255,255,.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s ease-in-out infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 PDF Merger</h1>
            <p class="subtitle">Upload multiple PDFs and merge them into one file</p>
            
            <div id="message" class="message hidden"></div>
            
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <p><strong>Click to upload</strong> or drag and drop</p>
                <p style="font-size: 12px; color: #999; margin-top: 5px;">PDF files only</p>
                <input type="file" id="fileInput" multiple accept=".pdf">
            </div>
            
            <div id="fileList" class="file-list"></div>
            
            <button class="btn btn-primary" id="mergeBtn" disabled>
                <span id="btnText">Merge PDFs</span>
                <span id="btnLoading" class="loading hidden"></span>
            </button>
        </div>
        
        <script>
            let files = [];
            
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const fileList = document.getElementById('fileList');
            const mergeBtn = document.getElementById('mergeBtn');
            const message = document.getElementById('message');
            const btnText = document.getElementById('btnText');
            const btnLoading = document.getElementById('btnLoading');
            
            uploadArea.addEventListener('click', () => fileInput.click());
            
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                handleFiles(e.dataTransfer.files);
            });
            
            fileInput.addEventListener('change', (e) => {
                handleFiles(e.target.files);
            });
            
            function handleFiles(newFiles) {
                const pdfFiles = Array.from(newFiles).filter(f => f.type === 'application/pdf');
                
                if (pdfFiles.length === 0) {
                    showMessage('Please select PDF files only', 'error');
                    return;
                }
                
                files.push(...pdfFiles);
                renderFileList();
                mergeBtn.disabled = files.length < 2;
                hideMessage();
            }
            
            function renderFileList() {
                fileList.innerHTML = files.map((file, idx) => `
                    <div class="file-item" draggable="true" data-index="${idx}">
                        <span class="file-name">${idx + 1}. ${file.name}</span>
                        <div class="file-controls">
                            <div class="order-controls">
                                <button class="btn btn-order" onclick="moveFile(${idx}, -1)" ${idx === 0 ? 'disabled' : ''}>↑</button>
                                <button class="btn btn-order" onclick="moveFile(${idx}, 1)" ${idx === files.length - 1 ? 'disabled' : ''}>↓</button>
                            </div>
                            <button class="btn btn-small" onclick="removeFile(${idx})">✕</button>
                        </div>
                    </div>
                `).join('');
                
                addDragListeners();
            }
            
            function addDragListeners() {
                const items = document.querySelectorAll('.file-item');
                items.forEach(item => {
                    item.addEventListener('dragstart', handleDragStart);
                    item.addEventListener('dragover', handleDragOver);
                    item.addEventListener('drop', handleDrop);
                    item.addEventListener('dragend', handleDragEnd);
                });
            }
            
            let draggedIdx = null;
            
            function handleDragStart(e) {
                draggedIdx = parseInt(e.target.dataset.index);
                e.target.style.opacity = '0.4';
            }
            
            function handleDragOver(e) {
                e.preventDefault();
                return false;
            }
            
            function handleDrop(e) {
                e.stopPropagation();
                e.preventDefault();
                
                const dropIdx = parseInt(e.target.closest('.file-item').dataset.index);
                
                if (draggedIdx !== dropIdx) {
                    const draggedFile = files[draggedIdx];
                    files.splice(draggedIdx, 1);
                    files.splice(dropIdx, 0, draggedFile);
                    renderFileList();
                }
                
                return false;
            }
            
            function handleDragEnd(e) {
                e.target.style.opacity = '1';
                draggedIdx = null;
            }
            
            function moveFile(idx, direction) {
                const newIdx = idx + direction;
                if (newIdx < 0 || newIdx >= files.length) return;
                
                [files[idx], files[newIdx]] = [files[newIdx], files[idx]];
                renderFileList();
            }
            
            function removeFile(idx) {
                files.splice(idx, 1);
                renderFileList();
                mergeBtn.disabled = files.length < 2;
                
                if (files.length === 0) {
                    fileInput.value = '';
                }
            }
            
            function showMessage(text, type) {
                message.textContent = text;
                message.className = `message ${type}`;
                message.classList.remove('hidden');
            }
            
            function hideMessage() {
                message.classList.add('hidden');
            }
            
            mergeBtn.addEventListener('click', async () => {
                if (files.length < 2) {
                    showMessage('Please select at least 2 PDF files', 'error');
                    return;
                }
                
                const formData = new FormData();
                files.forEach(file => formData.append('files', file));
                
                mergeBtn.disabled = true;
                btnText.classList.add('hidden');
                btnLoading.classList.remove('hidden');
                
                try {
                    const response = await fetch('/merge', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error('Merge failed');
                    }
                    
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `merged_${Date.now()}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    
                    showMessage('PDFs merged successfully!', 'success');
                    
                    setTimeout(() => {
                        files = [];
                        renderFileList();
                        fileInput.value = '';
                        hideMessage();
                    }, 2000);
                    
                } catch (error) {
                    showMessage('Error merging PDFs. Please try again.', 'error');
                } finally {
                    mergeBtn.disabled = false;
                    btnText.classList.remove('hidden');
                    btnLoading.classList.add('hidden');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files are required")
    
    # Verify all files are PDFs
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
    
    try:
        # Create PDF merger
        merger = PyPDF2.PdfMerger()
        
        # Read and merge all PDFs in order
        for file in files:
            content = await file.read()
            pdf_stream = io.BytesIO(content)
            merger.append(pdf_stream)
        
        # Write merged PDF to bytes
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        
        # Return as downloadable file
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)