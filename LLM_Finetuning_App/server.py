from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import os
import pipmaster as pm
import json
from pathlib import Path
import argparse
import uvicorn
if not pm.is_installed("torch"):
    pm.install_multiple(["torch","torchvision","torchaudio"], "https://download.pytorch.org/whl/cu121")
if not pm.is_installed("transformers"):
    pm.install("transformers")
if not pm.is_installed("datasets"):
    pm.install("datasets")
if not pm.is_installed("accelerate"):
    pm.install("accelerate")
if not pm.is_installed("peft"):
    pm.install("peft")
if not pm.is_installed("trl"):
    pm.install("trl")
if not pm.is_installed("bitsandbytes"):
    pm.install("bitsandbytes")

if not pm.is_installed("scipy"):
    pm.install_or_update("scipy")
if not pm.is_installed("threadpoolctl"):
    pm.install("threadpoolctl")


import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_8bit=True)

from enum import Enum

import transformers
import datasets
import accelerate
import peft
import trl
import bitsandbytes as bnb
from huggingface_hub import hf_hub_download


from ascii_colors import ASCIIColors, trace_exception


app = FastAPI()

# Create static folders if they don't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)
(static_dir / "images").mkdir(exist_ok=True)

# Mount static files directory under /static path
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add a root route to serve index.html
@app.get("/")
async def read_root():
    return FileResponse("index.html")


from pathlib import Path



# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class DatasetFormat(str, Enum):
    SINGLE_TEXT = "single_text"
    INSTRUCTION_INPUT_OUTPUT = "instruction_input_output"
    QUESTION_ANSWER = "question_answer"
    CUSTOM = "custom"
    LOLLMS = "lollms"  # New format for LoLLMs conversations

class TrainingConfig(BaseModel):
    model_name: str
    dataset_source: str
    dataset_name: str
    output_model_path: str  # Ajout du chemin de sortie du modèle
    dataset_format: DatasetFormat
    custom_format: str
    learning_rate: float = 3e-4
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    max_grad_norm: float = 0.3
    weight_decay: float = 0.001
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    lora_r: int = 8
    max_seq_length: int = 128000

class CustomCallback(transformers.TrainerCallback):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            await self.websocket.send_text(json.dumps({"log": str(logs)}))

    async def on_train_begin(self, args, state, control, **kwargs):
        await self.websocket.send_text(json.dumps({"log": "Training started"}))

    async def on_epoch_begin(self, args, state, control, **kwargs):
        await self.websocket.send_text(json.dumps({"log": f"Epoch {state.epoch} started"}))

    async def on_epoch_end(self, args, state, control, **kwargs):
        progress = (state.epoch / state.num_train_epochs) * 100
        await self.websocket.send_text(json.dumps({
            "progress": progress,
            "log": f"Epoch {state.epoch} completed"
        }))

    async def on_train_end(self, args, state, control, **kwargs):
        await self.websocket.send_text(json.dumps({
            "progress": 100,
            "log": "Training completed"
        }))

active_websockets = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        active_websockets.remove(websocket)



def preprocess_dataset(dataset, format: DatasetFormat, custom_format: Optional[str] = None):
    def process_example(example):
        if format == DatasetFormat.SINGLE_TEXT:
            return {"text": example["text"]}
        elif format == DatasetFormat.INSTRUCTION_INPUT_OUTPUT:
            return {"text": f"Instruction: {example['instruction']}\nInput: {example['input']}\nOutput: {example['output']}"}
        elif format == DatasetFormat.QUESTION_ANSWER:
            return {"text": f"Question: {example['question']}\nAnswer: {example['answer']}"}
        elif format == DatasetFormat.CUSTOM:
            if custom_format is None:
                raise ValueError("Custom format string must be provided for CUSTOM format")
            return {"text": custom_format.format(**example)}
        else:
            raise ValueError(f"Unsupported format: {format}")

    return dataset.map(process_example)



# Define a Pydantic model for the request body
class ModelDownloadRequest(BaseModel):
    model_name: str = Field(..., description="The Hugging Face model name in the format 'user/model_name'.")
    target_dir: str = Field(..., description="The directory where the model should be saved.")

@app.post("/download_model/")
async def download_model(request: ModelDownloadRequest):
    """
    Endpoint to download a Hugging Face model and store it in a specific directory.
    
    Args:
        request (ModelDownloadRequest): The request body containing model_name and target_dir.
    
    Returns:
        dict: A message indicating success or failure.
    """
    try:
        # Convert target_dir to a Path object
        target_path = Path(request.target_dir)
        
        # Ensure the target directory exists
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
        
        # Download the model and tokenizer
        model = transformers.AutoModel.from_pretrained(request.model_name, cache_dir=target_path)
        tokenizer = transformers.AutoTokenizer.from_pretrained(request.model_name, cache_dir=target_path)
        
        return {"message": f"Model '{request.model_name}' downloaded successfully to '{request.target_dir}'."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading model: {str(e)}")



@app.post("/train")
async def train_model(config: TrainingConfig):
    ASCIIColors.green("Training a model requested")
    try:
        ASCIIColors.green("1 - Loading model:")
        # Load the model
        model = transformers.AutoModelForCausalLM.from_pretrained(
            config.model_name,
            device_map="auto",
            torch_dtype="auto"
        )
        # Create a CustomCallback instance for each active WebSocket
        callbacks = [CustomCallback(ws) for ws in active_websockets]

        ASCIIColors.green("2 - Loading tokenizer:")
        # Load the tokenizer
        tokenizer = transformers.AutoTokenizer.from_pretrained(config.model_name)

        # Load the dataset
        if config.dataset_source == "huggingface":
            ASCIIColors.green("3 - Loading data from hugging face:")
            dataset = datasets.load_dataset(config.dataset_name)
        elif config.dataset_source == "local":
            ASCIIColors.green("3 - Loading data from local storage")
            dataset = datasets.load_dataset('json', data_files=str(config.dataset_name))
        else:
            raise HTTPException(status_code=400, detail="Invalid dataset source")
        
        # Preprocess the dataset
        ASCIIColors.green("4 - Preprocessing the dataset")
        preprocessed_dataset = preprocess_dataset(dataset, config.dataset_format, config.custom_format)        

        # Prepare the dataset
        def tokenize_function(examples):
            return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)

        ASCIIColors.green("5 - Tokenizing the data")
        tokenized_dataset = preprocessed_dataset.map(tokenize_function, batched=True)


        ASCIIColors.green("5 - Building trainer")
        # Prepare PEFT config
        peft_config = peft.LoraConfig(
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM"
        )

        # Prepare training arguments
        training_args = transformers.TrainingArguments(
            output_dir=Path(config.output_model_path).parent,
            learning_rate=config.learning_rate,
            num_train_epochs=config.num_train_epochs,
            per_device_train_batch_size=config.per_device_train_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            max_grad_norm=config.max_grad_norm,
            weight_decay=config.weight_decay
        )

        # Prepare the trainer
        trainer = trl.SFTTrainer(
            model=model,
            train_dataset=tokenized_dataset["train"],
            peft_config=peft_config,
            dataset_text_field="text",
            args=training_args,
            max_seq_length = config.max_seq_length,
            callbacks=callbacks  # Ajouter le callback personnalisé
        )


        ASCIIColors.green("6 - Starting training")
        # Start training
        trainer.train()

        ASCIIColors.green("7 - Saving fine tuned model")
        # Save the model
        trainer.model.save_pretrained(config.output_model_path)

        return {"message": "Training completed successfully"}

    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))


from peft import PeftModel
from typing import List

class FusionConfig(BaseModel):
    base_model_path: str
    lora_model_path: str
    output_path: str

@app.post("/fuse")
async def fuse_model(config: FusionConfig):
    try:
        ASCIIColors.green("Starting model fusion process")
        
        # Load the base model
        ASCIIColors.green("1 - Loading base model")
        base_model = transformers.AutoModelForCausalLM.from_pretrained(
            config.base_model_path,
            device_map="auto",
            torch_dtype="auto"
        )
        
        # Load the LoRA model
        ASCIIColors.green("2 - Loading LoRA model")
        model = PeftModel.from_pretrained(
            base_model,
            config.lora_model_path
        )
        
        # Merge LoRA weights with base model
        ASCIIColors.green("3 - Merging weights")
        model = model.merge_and_unload()
        
        # Save the merged model
        ASCIIColors.green("4 - Saving merged model")
        output_path = Path(config.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(output_path)
        
        # Save the tokenizer
        ASCIIColors.green("5 - Saving tokenizer")
        tokenizer = transformers.AutoTokenizer.from_pretrained(config.base_model_path)
        tokenizer.save_pretrained(output_path)
        
        # Send success message through WebSocket
        for websocket in active_websockets:
            await websocket.send_text(json.dumps({
                "status": "success",
                "message": "Model fusion completed successfully"
            }))
        
        return {"message": "Model fusion completed successfully", "output_path": str(output_path)}
    
    except Exception as e:
        trace_exception(e)
        # Send error message through WebSocket
        for websocket in active_websockets:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": str(e)
            }))
        raise HTTPException(status_code=500, detail=str(e))


class QuantizationConfig(BaseModel):
    model_path: str
    output_path: str
    quantization_bits: int = 8  # Default to 8-bit quantization

@app.post("/quantize")
async def quantize_model_endpoint(config: QuantizationConfig):
    try:
        ASCIIColors.green("Starting model quantization process")
        
        # Load the model
        ASCIIColors.green("1 - Loading and quantizing model")
        quantization_config = BitsAndBytesConfig(load_in_8bit=True if config.quantization_bits==8 else False, load_in_4bit=True if config.quantization_bits==4 else False)

        quantized_model = AutoModelForCausalLM.from_pretrained(
            config.model_path, 
            quantization_config=quantization_config
        )
        
        # Save the quantized model
        ASCIIColors.green("3 - Saving quantized model")
        output_path = Path(config.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        quantized_model.save_pretrained(output_path)
        
        # Save the tokenizer
        ASCIIColors.green("4 - Saving tokenizer")
        tokenizer = transformers.AutoTokenizer.from_pretrained(config.model_path)
        tokenizer.save_pretrained(output_path)
        
        # Send success message through WebSocket
        for websocket in active_websockets:
            await websocket.send_text(json.dumps({
                "status": "success",
                "message": f"Model quantization to {config.quantization_bits} bits completed successfully"
            }))
        
        return {"message": f"Model quantization to {config.quantization_bits} bits completed successfully", "output_path": str(output_path)}
    
    except Exception as e:
        trace_exception(e)
        # Send error message through WebSocket
        for websocket in active_websockets:
            await websocket.send_text(json.dumps({
                "status": "error",
                "message": str(e)
            }))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Run a Uvicorn server with configurable host and port.")
    
    # Add arguments for host and port with default values
    parser.add_argument('--host', type=str, default='localhost', help='Host to run the server on (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    
    # Parse the arguments
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
