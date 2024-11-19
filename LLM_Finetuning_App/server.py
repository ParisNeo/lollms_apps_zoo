from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict
import asyncio
import os
import pipmaster as pm
import json
from pathlib import Path
import argparse
import uvicorn
import os
import random

cuda_version = os.getenv("CUDA_VERSION", "cu121")
cuda_index = f"https://download.pytorch.org/whl/{cuda_version}"

if not pm.is_installed("torch"):
    pm.install_multiple(["torch","torchvision","torchaudio", "xformers"], cuda_index)
if not pm.is_installed("transformers"):
    pm.install("transformers", cuda_index)
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

if not pm.is_installed("protobuf"):
    pm.install("protobuf")

from peft import PeftModel
from typing import List
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
        elif format == DatasetFormat.LOLLMS:
            personality = "lollms"            
            if len(example["messages"])>1:
                found = False

                i = 0
                while not found and i<len(example["messages"]):
                    message = example["messages"][i]
                    if message['sender'] in message['personality']:
                        personality = message['sender']
                        found = True
                    i+=1
            discussion = f"!@>system: Act as a helpful assistant named {personality}\n"
            for message in example["messages"]:
                discussion += f"!@>{message['sender']}:{message['content']}\n"
            
            discussion += f"!@>"
            return {"text": discussion}
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



class PreprocessConfig(BaseModel):
    dataset_source: str  # "huggingface" or "local"
    dataset_name: str  # Dataset name or path
    dataset_format: str  # Format of the dataset (e.g., "custom", "lollms")
    custom_format: Optional[str] = None  # Optional custom format
    output_dataset_path: str  # Path to save the preprocessed dataset

@app.post("/preprocess")
async def preprocess_dataset_endpoint(config: PreprocessConfig):
    ASCIIColors.green("Preprocessing dataset requested")
    try:
        ASCIIColors.yellow("Using")
        # Load the dataset
        if config.dataset_source == "huggingface":
            ASCIIColors.green(f"1 - Loading data from Hugging Face: {config.dataset_name}")
            dataset = datasets.load_dataset(config.dataset_name)
        elif config.dataset_source == "local":
            ASCIIColors.green(f"1 - Loading data from local storage: {config.dataset_name}")
            dataset = datasets.load_dataset('json', data_files=str(config.dataset_name))
        else:
            raise HTTPException(status_code=400, detail="Invalid dataset source")

        # Preprocess the dataset
        ASCIIColors.green("2 - Preprocessing the dataset")
        preprocessed_dataset = preprocess_dataset(dataset, config.dataset_format, config.custom_format)

        # Convert the preprocessed dataset to a list of dictionaries with a 'text' field
        ASCIIColors.green("3 - Converting dataset to JSON format")
        json_data = []
        for entry in preprocessed_dataset['train']:
            json_data.append({"text": entry["text"]})

        # Save the JSON data to the output path
        output_path = Path(config.output_dataset_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        ASCIIColors.green(f"4 - Saving dataset to: {output_path}")
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        ASCIIColors.green(f"5 - Preprocessed dataset saved to {config.output_dataset_path}")
        return {"message": "Dataset preprocessed and saved successfully"}

    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))


class FuseDatasetsConfig(BaseModel):
    dataset1_path: str  # Path to the first preprocessed dataset
    dataset2_path: str  # Path to the second preprocessed dataset
    output_dataset_path: str  # Path to save the fused dataset

@app.post("/fuse_datasets")
async def fuse_datasets(config: FuseDatasetsConfig):
    ASCIIColors.green("Fusing datasets requested")
    try:
        # Load the preprocessed datasets
        ASCIIColors.green("1 - Loading preprocessed datasets")
        dataset1 = datasets.load_from_disk(config.dataset1_path)
        dataset2 = datasets.load_from_disk(config.dataset2_path)

        # Fuse the datasets
        ASCIIColors.green("2 - Fusing datasets")
        fused_dataset = datasets.concatenate_datasets([dataset1, dataset2])

        # Convert the fused dataset to a list of dictionaries
        fused_dataset_list = [dict(row) for row in fused_dataset]

        # Save the fused dataset as a JSON file
        output_path = Path(config.output_dataset_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(fused_dataset_list, f, ensure_ascii=False, indent=4)

        ASCIIColors.green(f"3 - Fused dataset saved to {config.output_dataset_path}")
        return {"message": "Datasets fused and saved successfully"}

    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))

class TrainingConfig(BaseModel):
    model_name: str
    dataset_source: str
    dataset_name: str
    dataset_format: str
    custom_format: Optional[str] = None
    output_model_path: str
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
    gpu_ids: Optional[List[int]] = None
    max_memory_per_gpu: Optional[Dict[int, str]] = None
    max_cpu_memory: Optional[str] = None
    fp16: bool = False
    training_method: str = "lora"  # New parameter for training method
    do_validation: bool = False  # New parameter to enable validation
    export_best_model_only: bool = False  # New parameter to export only the best model

    @field_validator('gpu_ids', mode='before')
    @classmethod
    def validate_gpu_ids(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return [int(id) for id in v if id is not None and id != '']
        return None

@app.post("/train")
async def train_model(config: TrainingConfig):
    ASCIIColors.green("Training a model requested")
    try:
        ASCIIColors.green("1 - Loading model:")
        # Prepare device map and max memory settings
        device_map = "auto"
        max_memory = None
        if config.gpu_ids is not None and len(config.gpu_ids) > 0:
            device_map = {i: i for i in config.gpu_ids}
        if config.max_memory_per_gpu is not None or config.max_cpu_memory is not None:
            max_memory = config.max_memory_per_gpu or {}
            if config.max_cpu_memory and config.max_cpu_memory != '':
                max_memory["cpu"] = config.max_cpu_memory

        # Load the model with GPU and memory configurations
        model = transformers.AutoModelForCausalLM.from_pretrained(
            config.model_name,
            device_map=device_map,
            max_memory=max_memory,
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
        ASCIIColors.green("Training sample for reference: ")
        random_entry = random.choice(preprocessed_dataset['train'])
        print(random_entry["text"])        
        ASCIIColors.green("\n\n\n")
        # Prepare the dataset
        def tokenize_function(examples):
            # Tokenize the input text
            tokenized_inputs = tokenizer(examples["text"], truncation=True, padding="max_length", max_length=512)
            
            # For causal language models, the labels are the same as the input_ids
            tokenized_inputs["labels"] = tokenized_inputs["input_ids"].copy()
            
            return tokenized_inputs

        ASCIIColors.green("5 - Tokenizing the data")
        tokenized_dataset = preprocessed_dataset.map(tokenize_function, batched=True)

        ASCIIColors.green("5 - Building trainer")


        # Ensure that if load_best_model_at_end is True, both evaluation and save strategies are aligned
        if config.export_best_model_only and not config.do_validation:
            raise ValueError("--export_best_model_only requires validation to be enabled.")
        
        # Prepare PEFT config if LoRA is selected
        if config.training_method == "lora":
            peft_config = peft.LoraConfig(
                r=config.lora_r,
                lora_alpha=config.lora_alpha,
                lora_dropout=config.lora_dropout,
                bias="none",
                task_type="CAUSAL_LM"
            )
        else:
            peft_config = None  # No PEFT config for full fine-tuning

        # Prepare training arguments
        training_args = transformers.TrainingArguments(
            output_dir=Path(config.output_model_path).parent,
            learning_rate=config.learning_rate,
            num_train_epochs=config.num_train_epochs,
            per_device_train_batch_size=config.per_device_train_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            max_grad_norm=config.max_grad_norm,
            weight_decay=config.weight_decay,
            # Add GPU-related arguments
            no_cuda=len(config.gpu_ids) == 0 if config.gpu_ids is not None else False,
            fp16=config.fp16,  # Enable mixed precision training
            
            eval_strategy="steps" if config.do_validation else "no",  # Enable validation if requested
            save_strategy="steps" if config.export_best_model_only else "epoch",  # Save only the best model if requested
            load_best_model_at_end=config.export_best_model_only  # Load the best model at the end if requested
        )

        # Prepare the trainer
        if config.training_method == "lora":
            trainer = trl.SFTTrainer(
                model=model,
                train_dataset=tokenized_dataset["train"],
                peft_config=peft_config,
                dataset_text_field="text",
                args=training_args,
                max_seq_length=config.max_seq_length,
                callbacks=callbacks
            )
        else:
            trainer = transformers.Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset["train"],
                eval_dataset=tokenized_dataset["validation"] if config.do_validation else None,
                tokenizer=tokenizer,
                callbacks=callbacks
            )

        ASCIIColors.green("6 - Starting training")
        # Start training
        trainer.train()

        ASCIIColors.green("7 - Saving fine-tuned model")
        # Save the model
        trainer.model.save_pretrained(config.output_model_path)

        return {"message": "Training completed successfully"}

    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))


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
    quantization_bits: str = "q8_0"  # Default to 8-bit quantization
    quantization_tool: str = "bitsandbytes" # Default is bitsand bytes

@app.post("/quantize")
async def quantize_model_endpoint(config: QuantizationConfig):
    try:
        ASCIIColors.green("Starting model quantization process")
        if config.quantization_tool=="bitsandbytes":
            # Load the model
            ASCIIColors.green("1 - Loading and quantizing model")
            quantization_config = BitsAndBytesConfig(load_in_8bit=True if config.quantization_bits=="q8_0" else False, load_in_4bit=True if config.quantization_bits=="q4_0" else False)

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
        elif config.quantization_tool=="gguf":
            if not pm.is_installed("llama_cpp"):
                import platform
                os_name = platform.system()
                if os_name == 'Windows':
                    print("This is a windows system")
                    pm.install("https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.2/llama_cpp_python-0.3.2-cp311-cp311-win_amd64.whl")
                elif os.name == 'Linux':
                    print("This is a linux system")
                    pm.install("https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.2/llama_cpp_python-0.3.2-cp311-cp311-linux_x86_64.whl")
                    print("Installing the linux version may require you to manually install musl-dev using:\napt install musl-dev\nln -s /usr/lib/x86_64-linux-musl/libc.so /lib/libc.musl-x86_64.so.1")
                elif os.name == 'Darwin':
                    print("This is a mac os system")
                    pm.install("https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.2/llama_cpp_python-0.3.2-cp311-cp311-macosx_10_9_x86_64.whl")
            import llama_cpp
            from llama_cpp import llama_model_quantize_params
            # Define the mapping between quantization_bits and LLAMA_FTYPE
            quantization_to_ftype = {
                'f32': 0,
                'f16': 1,
                'q4_0': 2,
                'q4_1': 3,
                'q8_0': 7,
                'q5_0': 8,
                'q5_1': 9,
                'q2_k': 10,
                'q3_k_s': 11,
                'q3_k_m': 12,
                'q3_k_l': 13,
                'q4_k_s': 14,
                'q4_k_m': 15,
                'q5_k_s': 16,
                'q5_k_m': 17,
                'q6_k': 18,
                'iq2_xxs': 19,
                'iq2_xs': 20,
                'q2_k_s': 21,
                'iq3_xs': 22,
                'iq3_xxs': 23,
                'fast_quantized': 1024,  # Assuming 'fast_quantized' is guessed
                'quantized': 1024,       # Assuming 'quantized' is guessed
                'q3_k_xs': 11            # Assuming 'q3_k_xs' maps to the same as 'q3_k_s'
            }
            result = llama_cpp.llama_model_quantize(config.model_path.encode("utf-8"), output_path.encode("utf-8"), llama_model_quantize_params(0),quantization_to_ftype[config.quantization_bits],True, True, False)
        else:
            ASCIIColors.error("Unknown tool!!")
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
