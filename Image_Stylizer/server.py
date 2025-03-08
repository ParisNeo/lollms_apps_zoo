import io
import base64
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionControlNetPipeline, ControlNetModel
import torch
from PIL import Image
import cv2
import numpy as np
import os

# Initialize FastAPI app
app = FastAPI(title="Portrait Stylization Server")

# Serve static files (place index.html in a 'static' folder)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load models
model_id = "runwayml/stable-diffusion-v1-5"
controlnet_id = "lllyasviel/sd-controlnet-canny"
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    model_id, controlnet=ControlNetModel.from_pretrained(controlnet_id), torch_dtype=torch.float16
)
device = "cuda" if torch.cuda.is_available() else "cpu"
pipe = pipe.to(device)

# Serve the HTML UI at the root
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/stylize/")
async def stylize_portrait(file: UploadFile, style_file: UploadFile = None, prompt: str = None):
    try:
        # Read and process the portrait image
        image_data = await file.read()
        init_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        init_image = init_image.resize((512, 512))

        # Prepare ControlNet condition (Canny edges)
        init_array = np.array(init_image)
        canny_image = cv2.Canny(init_array, 100, 200)
        canny_image = Image.fromarray(canny_image)

        if style_file:
            style_data = await style_file.read()
            style_image = Image.open(io.BytesIO(style_data)).convert("RGB").resize((512, 512))
            prompt = prompt or "stylized portrait"  # Fallback prompt
        elif not prompt:
            prompt = "in the style of a modern painting"

        # Generate stylized image
        stylized_image = pipe(
            prompt=prompt,
            image=init_image,
            controlnet_conditioning_image=canny_image,
            strength=0.75,
            guidance_scale=7.5,
            num_inference_steps=50,
            controlnet_conditioning_scale=0.7
        ).images[0]

        # Convert to base64
        buffered = io.BytesIO()
        stylized_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return JSONResponse(content={"stylized_image": f"data:image/png;base64,{img_str}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Ensure 'static' directory exists
    if not os.path.exists("static"):
        os.makedirs("static")
    uvicorn.run(app, host="0.0.0.0", port=8000)