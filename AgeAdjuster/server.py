from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
import io
import base64
import numpy as np
from pathlib import Path
import requests

import pipmaster as pm
pm.install_if_missing("antialiased-cnns")
pm.install_if_missing("mediapipe")

import antialiased_cnns
import mediapipe as mp
from typing import Optional
import os

app = FastAPI()

# UNet model from provided code
class DownLayer(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(DownLayer, self).__init__()
        self.layer = nn.Sequential(
            nn.MaxPool2d(kernel_size=2, stride=1),
            antialiased_cnns.BlurPool(in_channels, stride=2),
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True)
        )

    def forward(self, x):
        return self.layer(x)

class UpLayer(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(UpLayer, self).__init__()
        self.blur_upsample = nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2, padding=0),
            antialiased_cnns.BlurPool(out_channels, stride=1)
        )
        self.layer = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True)
        )

    def forward(self, x, skip):
        x = self.blur_upsample(x)
        x = torch.cat([x, skip], dim=1)
        return self.layer(x)

class UNet(nn.Module):
    def __init__(self):
        super(UNet, self).__init__()
        self.init_conv = nn.Sequential(
            nn.Conv2d(5, 64, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.LeakyReLU(inplace=True)
        )
        self.down1 = DownLayer(64, 128)
        self.down2 = DownLayer(128, 256)
        self.down3 = DownLayer(256, 512)
        self.down4 = DownLayer(512, 1024)
        self.up1 = UpLayer(1024, 512)
        self.up2 = UpLayer(512, 256)
        self.up3 = UpLayer(256, 128)
        self.up4 = UpLayer(128, 64)
        self.final_conv = nn.Conv2d(64, 3, kernel_size=1)

    def forward(self, x):
        x0 = self.init_conv(x)
        x1 = self.down1(x0)
        x2 = self.down2(x1)
        x3 = self.down3(x2)
        x4 = self.down4(x3)
        x = self.up1(x4, x3)
        x = self.up2(x, x2)
        x = self.up3(x, x1)
        x = self.up4(x, x0)
        x = self.final_conv(x)
        return torch.tanh(x)

# Sliding window utility
def sliding_window_tensor(input_tensor, window_size, stride, model):
    h, w = input_tensor.shape[2], input_tensor.shape[3]
    output = torch.zeros(1, 3, h, w, device=input_tensor.device)
    for i in range(0, h - window_size + 1, stride):
        for j in range(0, w - window_size + 1, stride):
            patch = input_tensor[:, :, i:i+window_size, j:j+window_size]
            with torch.no_grad():
                aged_patch = model(patch)
            output[:, :, i:i+window_size, j:j+window_size] = aged_patch
    return output

# Model wrapper with MediaPipe face extraction
class UNetAgeModel:
    def __init__(self, model_path: str = "models/best_unet_model.pth"):
        model_path_ = Path(model_path)
        if not model_path_.exists():

            # URL of the file to download
            url = "https://huggingface.co/timroelofs123/face_re-aging/resolve/main/best_unet_model.pth?download=true"

            # Define the models subfolder using pathlib
            models_folder = Path("models")
            models_folder.mkdir(parents=True, exist_ok=True)  # Create the folder if it doesn't exist

            # Define the full path to save the downloaded file
            file_path = models_folder / "best_unet_model.pth"

            # Download the file
            try:
                print("Downloading file...")
                response = requests.get(url, stream=True)
                response.raise_for_status()  # Raise an error for bad status codes

                # Save the file
                with open(file_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                print(f"File downloaded and saved to: {file_path}")

            except requests.exceptions.RequestException as e:
                print(f"Error downloading file: {e}")
            pass

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = UNet().to(self.device)
        self.load_weights(model_path)
        self.input_size = (1024, 1024)
        self.window_size = 512
        self.stride = 256
        self.face_detector = mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)
        print(f"UNet model loaded on {self.device}")

    def load_weights(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weights not found at {model_path}")
        state_dict = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def estimate_age(self, image: Image.Image) -> int:
        return 40  # Placeholder

    def process_image(self, image: Image.Image, source_age: int, target_age: int) -> Image.Image:
        # Convert to numpy for MediaPipe
        image_np = np.array(image)
        h, w = image_np.shape[:2]
        
        # Detect face with MediaPipe
        results = self.face_detector.process(image_np)
        if not results.detections:
            raise ValueError("No face detected in the image")
        
        # Get bounding box (first detection)
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box
        x_min = int(bbox.xmin * w)
        y_min = int(bbox.ymin * h)
        box_w = int(bbox.width * w)
        box_h = int(bbox.height * h)

        # Calculate margins
        margin_y_t = int(box_h * 0.63 * 0.85)
        margin_y_b = int(box_h * 0.37 * 0.85)
        margin_x = int(box_w / 2 * 0.85)
        margin_y_t += 2 * margin_x - margin_y_t - margin_y_b

        l_y = max([y_min - margin_y_t, 0])
        r_y = min([y_min + box_h + margin_y_b, h])
        l_x = max([x_min - margin_x, 0])
        r_x = min([x_min + box_w + margin_x, w])

        # Crop image
        cropped_image = image_np[l_y:r_y, l_x:r_x, :]
        orig_size = cropped_image.shape[:2]

        # Prepare tensor, ensuring all are on the same device
        cropped_tensor = transforms.ToTensor()(cropped_image).to(self.device)
        cropped_resized = transforms.Resize(self.input_size, interpolation=transforms.InterpolationMode.BILINEAR, antialias=True)(cropped_tensor)
        source_age_channel = torch.full_like(cropped_resized[:1, :, :], source_age / 100).to(self.device)
        target_age_channel = torch.full_like(cropped_resized[:1, :, :], target_age / 100).to(self.device)
        input_tensor = torch.cat([cropped_resized, source_age_channel, target_age_channel], dim=0).unsqueeze(0).to(self.device)

        # Process with sliding window
        aged_cropped_image = sliding_window_tensor(input_tensor, self.window_size, self.stride, self.model)

        # Resize back and re-apply
        aged_cropped_resized = transforms.Resize(orig_size, interpolation=transforms.InterpolationMode.BILINEAR, antialias=True)(aged_cropped_image)
        image_tensor = transforms.ToTensor()(image_np).to(self.device)
        image_tensor[:, l_y:r_y, l_x:r_x] += aged_cropped_resized.squeeze(0)
        image_tensor = torch.clamp(image_tensor, 0, 1)

        return transforms.functional.to_pil_image(image_tensor.cpu())  # Move back to CPU for PIL conversion

# Initialize model
try:
    model = UNetAgeModel()
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

@app.get("/", response_class=HTMLResponse)
async def get_html():
    with open("index.html", "r") as f:
        return f.read()

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not model:
        return {"error": "Model not loaded"}
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    initial_age = model.estimate_age(image)
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return {"image": img_str, "initial_age": initial_age}

@app.post("/adjust_age")
async def adjust_age(file: UploadFile = File(...), source_age: int = Form(...), target_age: int = Form(...)):
    print(f"Received source_age: {source_age}, target_age: {target_age}")
    if not model:
        return {"error": "Model not loaded"}
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    try:
        adjusted_image = model.process_image(image, source_age, target_age)
    except ValueError as e:
        return {"error": str(e)}
    buffered = io.BytesIO()
    adjusted_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return {"image": img_str}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)