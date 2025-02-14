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
import asyncio
import json


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
from transformers import TrainerCallback

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
    LOLLMS_SMART_ROUTER  = "lollms_smart_router"
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
        elif format == DatasetFormat.LOLLMS_SMART_ROUTER:
            return {"text": f"""!@>system:
{example['task_prompt']}
Given the prompt, which model among the previous list is the most suited and why?

You must answer with json code placed inside the markdown code tag like this:
```json
{{
    "choice_index": [an int representing the index of the choice made]
    "justification": "[Justify the choice]",
}}
```
Make sure you fill all fields and to use the exact same keys as the template.
Don't forget encapsulate the code inside a markdown code tag. This is mandatory.

!@>assistant:"""+"""
```json
{
    "choice_index": """+example['task_solution']+","+"""
    "justification": """+example['explanation']+"""
}
```
!@>
"""}
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
    model_config = {
        "protected_namespaces": ()
    }

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
    dataset1_source: str # the dataset source (hugging face or local)
    dataset1_path: str  # Path to the first preprocessed dataset
    dataset2_source: str # the dataset source (hugging face or local)
    dataset2_path: str  # Path to the second preprocessed dataset
    output_dataset_path: str  # Path to save the fused dataset
@app.post("/fuse_datasets")
async def fuse_datasets(config: FuseDatasetsConfig):
    ASCIIColors.green("Fusing datasets requested")
    try:
        # Check if both datasets are local
        both_local = (config.dataset1_source == "local" and 
                     config.dataset2_source == "local")
        
        if both_local:
            # Direct JSON fusion for local datasets
            ASCIIColors.green("1 - Loading and fusing local JSON datasets")
            with open(config.dataset1_path, 'r', encoding='utf-8') as f1:
                dataset1 = json.load(f1)
            with open(config.dataset2_path, 'r', encoding='utf-8') as f2:
                dataset2 = json.load(f2)
                
            # Combine the JSON data directly
            fused_dataset_list = dataset1 + dataset2
            
        else:
            # Original HuggingFace dataset loading logic
            ASCIIColors.green("1 - Loading preprocessed datasets")
            # Load dataset 1
            if config.dataset1_source == "huggingface":
                dataset1 = datasets.load_dataset(config.dataset1_path)
            else:
                dataset1 = datasets.load_dataset('json', data_files=str(config.dataset1_path))
                
            # Load dataset 2
            if config.dataset2_source == "huggingface":
                dataset2 = datasets.load_dataset(config.dataset2_path)
            else:
                dataset2 = datasets.load_dataset('json', data_files=str(config.dataset2_path))
            
            ASCIIColors.green("2 - Fusing datasets")
            fused_dataset = datasets.concatenate_datasets([dataset1, dataset2])
            fused_dataset_list = [dict(row) for row in fused_dataset]

        # Save the fused dataset
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

    model_config = {
        "protected_namespaces": ()
    }

    @field_validator('gpu_ids', mode='before')
    @classmethod
    def validate_gpu_ids(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            return [int(id) for id in v if id is not None and id != '']
        return None

import json
import asyncio
from typing import Optional

class DetailedCallback(TrainerCallback):
    def __init__(self, ws=None):
        self.ws = ws
        self.current_step = 0
        self.logging_steps = 0
        self.best_loss = float('inf')
        self.loop = asyncio.get_event_loop() if ws else None

    def on_train_begin(self, args, state, control, **kwargs):
        ASCIIColors.green("\n=== Training Started ===")
        ASCIIColors.green(f"Total Steps: {state.max_steps}")
        ASCIIColors.green("Initial learning rate: {}\n".format(args.learning_rate))
        self.logging_steps = args.logging_steps

    def on_step_end(self, args, state, control, **kwargs):
        self.current_step = state.global_step

    async def _send_ws_message(self, message: str):
        """Async helper to send websocket messages"""
        if self.ws and self.ws.client_state.value == 1:  # Check if connection is still open
            try:
                await self.ws.send_text(message)
            except Exception as e:
                ASCIIColors.red(f"Error sending to websocket: {str(e)}")

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None:
            # Extract metrics
            loss = logs.get("loss", None)
            learning_rate = logs.get("learning_rate", None)
            epoch = logs.get("epoch", None)
            
            # Format the metrics string
            metrics_str = f"Step: {self.current_step}/{state.max_steps}"
            if loss is not None:
                metrics_str += f" | Loss: {loss:.4f}"
                if loss < self.best_loss:
                    self.best_loss = loss
                    metrics_str += " (Best)"
            if learning_rate is not None:
                metrics_str += f" | LR: {learning_rate:.2e}"
            if epoch is not None:
                metrics_str += f" | Epoch: {epoch:.2f}"
            
            # Add validation metrics if present
            eval_loss = logs.get("eval_loss", None)
            if eval_loss is not None:
                metrics_str += f" | Eval Loss: {eval_loss:.4f}"

            ASCIIColors.yellow(metrics_str)

            # Send to websocket if available
            if self.ws:
                message = {
                    "type": "training_progress",
                    "data": {
                        "step": self.current_step,
                        "total_steps": state.max_steps,
                        "loss": float(loss) if loss is not None else None,
                        "learning_rate": float(learning_rate) if learning_rate is not None else None,
                        "epoch": float(epoch) if epoch is not None else None,
                        "eval_loss": float(eval_loss) if eval_loss is not None else None,
                        "best_loss": float(self.best_loss)
                    }
                }
                
                # Send the message using a background task
                if self.loop and self.loop.is_running():
                    self.loop.create_task(self._send_ws_message(json.dumps(message)))

    def on_train_end(self, args, state, control, **kwargs):
        ASCIIColors.green("\n=== Training Completed ===")
        ASCIIColors.green(f"Best Loss: {self.best_loss:.4f}")



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
        class LossLoggerCallback(TrainerCallback):
            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs is not None and "loss" in logs:
                    ASCIIColors.green(f"Step {state.global_step}: Loss = {logs['loss']:.4f}")

        # Add the custom callback to the list of callbacks
        callbacks.append(LossLoggerCallback())

        ASCIIColors.green("2 - Loading tokenizer:")
        # Load the tokenizer
        tokenizer = transformers.AutoTokenizer.from_pretrained(config.model_name)
        # Set padding side to 'right' to avoid overflow issues in fp16 training
        tokenizer.padding_side = 'right'

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

        if config.do_validation:
            ASCIIColors.green("4.1 - Splitting dataset into train and validation")
            # Split only if dataset doesn't already have a validation split
            if "validation" not in preprocessed_dataset:
                # Split with 90% train, 10% validation
                split_dataset = preprocessed_dataset["train"].train_test_split(test_size=0.1, shuffle=True, seed=42)
                preprocessed_dataset = datasets.DatasetDict({
                    'train': split_dataset['train'],
                    'validation': split_dataset['test']
                })             
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
        training_args = trl.SFTConfig(
            dataset_text_field="text",
            max_seq_length=config.max_seq_length,

            output_dir=Path(config.output_model_path).parent,
            learning_rate=config.learning_rate,
            num_train_epochs=config.num_train_epochs,
            per_device_train_batch_size=config.per_device_train_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            max_grad_norm=config.max_grad_norm,
            weight_decay=config.weight_decay,
            no_cuda=len(config.gpu_ids) == 0 if config.gpu_ids is not None else False,
            fp16=config.fp16,
            
            # Add logging related arguments
            logging_steps=10,  # Log every 10 steps
            logging_first_step=True,  # Log the first step
            logging_dir=str(Path(config.output_model_path).parent / "logs"),
            logging_strategy="steps",
            
            # Evaluation settings
            eval_strategy="steps" if config.do_validation else "no",
            eval_steps=100 if config.do_validation else None,  # Evaluate every 100 steps
            save_strategy="steps" if config.export_best_model_only else "epoch",
            load_best_model_at_end=config.export_best_model_only
        )

        # Replace the callbacks list creation with:
        callbacks = [DetailedCallback(ws) for ws in active_websockets]

        # Prepare the trainer
        if config.training_method == "lora":
            trainer = trl.SFTTrainer(
                model=model,
                train_dataset=tokenized_dataset["train"],
                eval_dataset=tokenized_dataset["validation"] if config.do_validation else None,
                peft_config=peft_config,
                args=training_args,
                
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

class InferenceRequest(BaseModel):
    input_text: str
    model_path: str
    temperature: float = 0.1
    max_tokens: int = 2048
    device: str = "cuda:0"
    max_seq_length: int = 2048
    model_config: dict = {"protected_namespaces": ()}

class InferenceResponse(BaseModel):
    output_text: str

@app.post("/query", response_model=InferenceResponse)
async def query_endpoint(request: InferenceRequest):
    try:
        # Load the model
        model = AutoModelForCausalLM.from_pretrained(request.model_path)
        tokenizer = transformers.AutoTokenizer.from_pretrained(request.model_path)

        # Set device
        device = torch.device(request.device if torch.cuda.is_available() else "cpu")
        model.to(device)

        # Tokenize input with attention mask
        inputs = tokenizer(
            request.input_text,
            return_tensors="pt",
            max_length=request.max_seq_length,
            truncation=True,
            return_attention_mask=True
        )

        # Generate output with attention mask
        try:
            ASCIIColors.yellow('Starting generation')
            outputs = model.generate(
                input_ids=inputs["input_ids"].to(device),
                attention_mask=inputs["attention_mask"].to(device),
                do_sample=True,
                temperature=request.temperature,
                max_new_tokens=request.max_tokens
            )
            ASCIIColors.green('Generation done')
        except Exception as ex:
            trace_exception(ex)

        # Decode output
        output_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return InferenceResponse(output_text=output_text)

    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))


class FusionConfig(BaseModel):
    base_model_path: str
    lora_model_path: str
    output_path: str
    model_config = {
        "protected_namespaces": ()
    }

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
            try:
                await websocket.send_text(json.dumps({
                    "status": "success",
                    "message": "Model fusion completed successfully"
                }))
            except Exception as ex:
                trace_exception(ex)        
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
    model_config = {
        "protected_namespaces": ()
    }

from huggingface_hub import Repository
import torch

def push_model_to_hf(model, model_name, model_class, tokenizer=None, hf_username="your_username", hf_token="your_token"):
    """
    Push a trained model to Hugging Face model hub.
    
    Args:
        model: The trained model to push.
        model_name: The name of your model on Hugging Face.
        model_class: The class of your model (e.g., CausalLM).
        tokenizer: Optional tokenizer to push alongside the model.
        hf_username: Your Hugging Face username.
        hf_token: Your Hugging Face access token.
    """
    # Initialize the repository
    repo = Repository(
        local_dir="./",
        repo_type="model",
        repo_id=f"{hf_username}/{model_name}",
    )
    
    # Login using the access token
    repo.git_config.username = hf_username
    repo.git_config.password = hf_token
    
    # Create a model card if it doesn't exist
    model_card = f"""
    # {model_name}
    
    This is a causal language model trained on [your dataset or training details].
    """
    with open("model_card.md", "w") as f:
        f.write(model_card)
    
    # Save the model
    model.save_pretrained("./")
    
    # Push the model to Hugging Face
    repo.push_to_hub(commit_message=f"Initial commit of {model_name}")
    
    print(f"Model pushed successfully to https://huggingface.co/{hf_username}/{model_name}")

@app.post("/quantize")
async def quantize_model_endpoint(config: QuantizationConfig):
    try:
        ASCIIColors.green("Starting model quantization process")
        if config.quantization_tool=="bitsandbytes":
            output_path = Path(config.output_path)
            output_path.mkdir(parents=True, exist_ok=True)

            # Load the model
            ASCIIColors.green("1 - Loading and quantizing model")
            quantization_config = BitsAndBytesConfig(load_in_8bit=True if config.quantization_bits=="q8_0" else False, load_in_4bit=True if config.quantization_bits=="q4_0" else False)

            quantized_model = AutoModelForCausalLM.from_pretrained(
                config.model_path, 
                quantization_config=quantization_config
            )
            
            # Save the quantized model
            ASCIIColors.green("3 - Saving quantized model")
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
            output_path = Path(config.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
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
            result = llama_cpp.llama_model_quantize(config.model_path.encode("utf-8"), str(output_path).encode("utf-8"), llama_model_quantize_params(0),quantization_to_ftype[config.quantization_bits],True, True, False)
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

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

if __name__ == "__main__":
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Run a Uvicorn server with configurable host and port.")
    
    # Add arguments for host and port with default values
    parser.add_argument('--host', type=str, default='localhost', help='Host to run the server on (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    
    # Parse the arguments
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
