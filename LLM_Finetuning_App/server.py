import os
import sys
import asyncio
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Union, Any
from enum import Enum
import ascii_colors as logging # Using ascii_colors for logging
from ascii_colors import trace_exception, ProgressBar as ASCIIProgressBar # Import ProgressBar
from ascii_colors import ASCIIColors # Import ASCIIColors for constants if needed directly

# Set environment variables early, especially CUDA_VISIBLE_DEVICES
# Example: os.environ['CUDA_VISIBLE_DEVICES'] = '0'
# Or parse from args if needed

# Configure logging (ascii_colors.basicConfig is compatible with standard logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__) # Get a logger instance

# Suppress overly verbose logs from libraries
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("datasets").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

# --- FastAPI Imports ---
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator, validator # field_validator is modern, validator is older

# --- ML Imports ---
# pipmaster usage remains as is, assuming it handles installations correctly.
# pm.ensure_packages(...)
try:
    import torch
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer,
        BitsAndBytesConfig, HfArgumentParser, GenerationConfig,
        TrainerCallback, TrainerState, TrainerControl 
    )
    from datasets import load_dataset, Dataset, concatenate_datasets
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from huggingface_hub import HfApi, snapshot_download, login as hf_login
    import bitsandbytes as bnb 
    from accelerate import Accelerator 
except ImportError as e:
    trace_exception(e) # Log the exception using ascii_colors
    logger.error(f"Missing essential ML libraries. Please install requirements.txt: {e}")
    sys.exit(1)

# Check for GPU availability
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVIDIA_GPU = True
    gpu_count = pynvml.nvmlDeviceGetCount()
    logger.info(f"NVIDIA GPU(s) detected: {gpu_count}")
    pynvml.nvmlShutdown()
except Exception:
    HAS_NVIDIA_GPU = False
    logger.warning("NVIDIA GPU driver or pynvml not found. Running in CPU mode (if supported by model/task).")

# --- App Setup ---
app = FastAPI(title="LLM Finetuning App Backend")

# Create static folders if they don't exist
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
(static_dir / "css").mkdir(exist_ok=True)
(static_dir / "js").mkdir(exist_ok=True)
(static_dir / "images").mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_root():
    return FileResponse("index.html")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket Management ---
active_websockets: List[WebSocket] = []
main_event_loop: Optional[asyncio.AbstractEventLoop] = None

@app.on_event("startup")
async def startup_event():
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()
    logger.info("Captured main event loop for thread-safe operations.")

async def broadcast_message(message: Dict):
    """Sends a message to all connected WebSocket clients."""
    disconnected_sockets = []
    message_json = json.dumps(message)
    for websocket in active_websockets:
        try:
            await websocket.send_text(message_json)
        except WebSocketDisconnect:
            disconnected_sockets.append(websocket)
        except Exception as e:
            logger.error(f"Error sending message to websocket {websocket}: {e}")
            disconnected_sockets.append(websocket) 

    for ws in disconnected_sockets:
        if ws in active_websockets:
            active_websockets.remove(ws)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    logger.info(f"WebSocket connection established: {websocket.client}")
    try:
        while True:
            await asyncio.sleep(60) 
            await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocket error for {websocket.client}: {e}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

# --- Pydantic Models for API Requests (remain unchanged from original) ---
class DownloadModelRequest(BaseModel):
    model_name: str
    target_dir: Optional[str] = None

class PreprocessDatasetRequest(BaseModel):
    dataset_source: str 
    dataset_name: str 
    output_dataset_path: str
    dataset_format: str 
    custom_format: Optional[str] = None
    base_model_name: Optional[str] = None

    @validator('dataset_source')
    def source_must_be_valid(cls, v):
        if v not in ['huggingface', 'local']:
            raise ValueError('dataset_source must be "huggingface" or "local"')
        return v

class FuseDatasetsRequest(BaseModel):
    dataset1_source: str
    dataset1_path: str
    dataset2_source: str
    dataset2_path: str
    output_dataset_path: str

class TrainRequest(BaseModel):
    model_name: str
    dataset_source: str
    dataset_name: str
    output_model_path: str
    learning_rate: float = 2e-4
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 0.3
    weight_decay: float = 0.001
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_r: int = 8
    max_seq_length: int = 512
    gpu_ids: Optional[str] = None 
    fp16: bool = True
    training_method: str = 'lora' 

    @validator('training_method')
    def method_must_be_valid(cls, v):
        if v not in ['lora', 'full']:
            raise ValueError('training_method must be "lora" or "full"')
        return v

class FuseRequest(BaseModel):
    base_model_path: str
    lora_model_path: str
    output_path: str

class QueryRequest(BaseModel):
    model_path: str
    input_text: str
    max_new_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.9

class QuantizeRequest(BaseModel):
    model_path: str
    output_path: str
    quantization_tool: str 
    quantization_method: str 

    @validator('quantization_tool')
    def tool_must_be_valid(cls, v):
        if v not in ['bitsandbytes', 'gguf']:
            raise ValueError('quantization_tool must be "bitsandbytes" or "gguf"')
        return v

class PushToHFRequest(BaseModel):
    local_model_path: str
    hf_repo_name: str
    hf_username: Optional[str] = None 
    hf_token: str
    commit_message: str = "Upload model via LLM Finetuning App"
    private_repo: bool = False


# --- Helper Functions ---
async def send_log_via_ws(message: str, progress: Optional[float] = None, loss_data: Optional[Dict[str, Any]] = None):
    """Helper to send log messages, progress, and optional loss data via WebSocket (async)."""
    payload = {"log": message}
    if progress is not None:
        payload["progress"] = progress
    if loss_data is not None:
        payload["loss_update"] = loss_data # Add loss data here
    await broadcast_message(payload)

async def send_error(message: str):
    await broadcast_message({"error": message})
    logger.error(message) # Log server-side as well

async def send_completion(message: str = "Task completed successfully."):
    await broadcast_message({"status": "completed", "log": message, "progress": 100})
    logger.info(message) # Log server-side


def get_device_map() -> Union[str, Dict[int, int]]:
    if HAS_NVIDIA_GPU and torch.cuda.is_available():
        return "auto"
    else:
        return "cpu"

def _resolve_path(p: str) -> Path:
    return Path(p).resolve()


# --- Core Task Functions (Download, Preprocess, Fuse Datasets - remain largely unchanged) ---
async def run_download_model(req: DownloadModelRequest):
    try:
        await send_log_via_ws(f"Starting download for model: {req.model_name}", progress=0)
        target = _resolve_path(req.target_dir) if req.target_dir else None
        if target:
             target.mkdir(parents=True, exist_ok=True)

        download_path = snapshot_download(
            repo_id=req.model_name,
            local_dir=str(target) if target else None,
            local_dir_use_symlinks=False, 
            resume_download=True,
        )
        logger.info(f"Model {req.model_name} downloaded to {download_path}") 
        await send_completion(f"Model downloaded successfully to: {download_path}")
    except Exception as e:
        trace_exception(e)
        await send_error(f"Model download failed: {e}")

async def run_preprocess_dataset(req: PreprocessDatasetRequest):
    tokenizer = None # Initialize tokenizer
    try:
        await send_log_via_ws(f"Starting dataset preprocessing for: {req.dataset_name}", progress=0)
        output_path = _resolve_path(req.output_dataset_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # --- Load Tokenizer if base_model_name is provided ---
        if req.base_model_name:
            try:
                await send_log_via_ws(f"Loading tokenizer for: {req.base_model_name}...")
                # Consider adding trust_remote_code=True if needed for some models,
                # but be aware of security implications.
                tokenizer = AutoTokenizer.from_pretrained(req.base_model_name)
                if tokenizer.pad_token is None:
                    # Some models like Llama don't have a pad token by default
                    tokenizer.pad_token = tokenizer.eos_token 
                    await send_log_via_ws(f"Tokenizer for {req.base_model_name} missing pad_token, set to eos_token.")
                logger.info(f"Tokenizer for {req.base_model_name} loaded successfully.")
            except Exception as e:
                # You might want to make this a non-fatal error if templating is optional for some formats
                # or if base_model_name is truly optional.
                # For now, let's assume it's critical for the formats that need it.
                raise ValueError(f"Failed to load tokenizer for '{req.base_model_name}': {e}")
        else:
            # Warn if a format might need it but no model was provided
            chat_formats = ["question_answer", "instruction_input_output", "lollms"]
            if req.dataset_format in chat_formats:
                 await send_log_via_ws(
                     "Warning: base_model_name not provided. Chat templating will not be applied, "
                     "which might lead to suboptimal performance for chat/instruction models.", progress=5
                 )
                 logger.warning("base_model_name not provided for a chat-like format. Chat templating skipped.")


        await send_log_via_ws("Loading dataset...")
        logger.info(f"Preprocessing: Loading dataset {req.dataset_name} from {req.dataset_source}")
        # ... (rest of your dataset loading logic remains the same) ...
        if req.dataset_source == 'huggingface':
            try:
                dataset = load_dataset(req.dataset_name, split='train')
            except Exception as e:
                raise ValueError(f"Failed to load dataset '{req.dataset_name}' from Hugging Face: {e}")
        elif req.dataset_source == 'local':
            local_path = _resolve_path(req.dataset_name)
            if not local_path.exists():
                raise FileNotFoundError(f"Local dataset file not found: {local_path}")
            try:
                # Universal way to load from local path if it's a directory or common file types
                if local_path.is_dir():
                    dataset = load_dataset(str(local_path), split='train')
                elif local_path.suffix in ['.json', '.jsonl', '.csv']:
                    file_type = local_path.suffix[1:] # 'json', 'jsonl', 'csv'
                    if file_type == "jsonl": file_type = "json" # datasets library treats jsonl as json
                    dataset = load_dataset(file_type, data_files=str(local_path), split='train')
                else:
                    raise ValueError(f"Unsupported local file type: {local_path.suffix}. Use .json, .jsonl, .csv, or a directory.")
            except Exception as e:
                 raise ValueError(f"Failed to load local dataset '{local_path}': {e}")
        else:
            raise ValueError("Invalid dataset_source")

        await send_log_via_ws(f"Loaded dataset with {len(dataset)} examples.", progress=25)
        logger.info(f"Loaded dataset with {len(dataset)} examples for preprocessing.")

        def format_example(example: Dict[str, Any]) -> Dict[str, str]:
            try:
                # --- Helper for applying chat template ---
                def _apply_chat_template_if_tokenizer(messages: List[Dict[str, str]]) -> str:
                    if tokenizer:
                        try:
                            # add_generation_prompt=False is crucial for SFTTrainer as it expects the full sequence
                            # SFTTrainer itself might handle adding a generation prompt if needed for generation later.
                            # For training, we provide the full sequence including the target response.
                            return tokenizer.apply_chat_template(
                                messages,
                                tokenize=False,
                                add_generation_prompt=False # Usually False for SFT
                            )
                        except Exception as e:
                            logger.error(f"Error applying chat template: {e}. Falling back to basic formatting. Messages: {messages}")
                            # Fallback to basic formatting if templating fails
                            return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                    else:
                        # Fallback if no tokenizer (e.g., base_model_name not provided)
                        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

                if req.dataset_format == "single_text":
                    if "text" not in example: raise KeyError("'text' field missing")
                    return {"text": str(example["text"])}
                
                elif req.dataset_format == "instruction_input_output":
                    instr = example.get("instruction", "")
                    inp = example.get("input", "") # Input is optional for the user part
                    out = example.get("output", "") # Output is the assistant's response
                    if not instr or not out: raise KeyError("Missing 'instruction' or 'output'")
                    
                    messages = []
                    # System prompt can be part of the instruction or a separate field
                    # For simplicity, let's assume instruction might contain system-level directions.
                    # Or, you could have a "system" field in your input JSON.
                    # messages.append({"role": "system", "content": example.get("system", "You are a helpful assistant.")})

                    user_content = f"{instr}"
                    if inp: # If there's separate input, append it to the user's turn
                        user_content += f"\n\n### Input:\n{inp}"
                    
                    messages.append({"role": "user", "content": user_content})
                    messages.append({"role": "assistant", "content": out})
                    
                    return {"text": _apply_chat_template_if_tokenizer(messages)}

                elif req.dataset_format == "question_answer":
                    q = example.get("question", "")
                    a = example.get("answer", "")
                    if not q or not a: raise KeyError("Missing 'question' or 'answer'")
                    
                    messages = [
                        # Optional: You might want a system prompt here too
                        # {"role": "system", "content": "You answer questions accurately."},
                        {"role": "user", "content": q},
                        {"role": "assistant", "content": a}
                    ]
                    return {"text": _apply_chat_template_if_tokenizer(messages)}

                elif req.dataset_format == "lollms": # Assuming 'lollms' is a list of turns
                    # System prompt might be the first turn or a separate field
                    discussion_turns = example.get("discussion", []) # Expects a list of {"role": ..., "content": ...}
                    if not discussion_turns: raise KeyError("Missing 'discussion' list or it's empty")

                    # Construct messages list, ensuring correct roles
                    messages = []
                    if "system_prompt" in example and example["system_prompt"]:
                         messages.append({"role": "system", "content": str(example["system_prompt"])})
                    
                    for turn in discussion_turns:
                        role = str(turn.get("role", "user")).lower() # Normalize role
                        content = str(turn.get("content", ""))
                        if role not in ["user", "assistant", "system"]: # tool/function roles also exist
                            logger.warning(f"Unknown role '{role}' in lollms format, treating as 'user'. Content: {content[:50]}...")
                            role = "user" # Or skip, or handle appropriately
                        messages.append({"role": role, "content": content})
                    
                    if not any(msg['role'] == 'assistant' for msg in messages):
                        raise ValueError("Lollms discussion format must contain at least one assistant turn for SFT.")

                    return {"text": _apply_chat_template_if_tokenizer(messages)}
                
                elif req.dataset_format == "lollms_smart_router": # Assumed to be already formatted text
                    if "text" not in example: raise KeyError("'text' field missing for lollms_smart_router")
                    return {"text": str(example["text"])}

                elif req.dataset_format == "custom":
                    if not req.custom_format: raise ValueError("Custom format string is required")
                    # Custom format might not use chat templating unless you design it to.
                    # If req.custom_format is something like "USER: {q} ASSISTANT: {a}",
                    # it bypasses the _apply_chat_template_if_tokenizer.
                    # This is fine if the user provides a fully templated custom string.
                    return {"text": req.custom_format.format(**example)}
                else:
                    raise ValueError(f"Unknown dataset format: {req.dataset_format}")
            except KeyError as e:
                raise ValueError(f"Missing required field {e} in example for format '{req.dataset_format}'. Example keys: {list(example.keys())}")
            except Exception as e:
                 raise ValueError(f"Error formatting example: {str(e)}. Example data: {str(example)[:500]}")


        await send_log_via_ws("Applying formatting...", progress=50)
        logger.info("Preprocessing: Applying formatting.")
        # Ensure remove_columns correctly uses the original dataset's column names
        original_columns = list(dataset.column_names)
        processed_dataset = dataset.map(format_example, remove_columns=original_columns)

        # ... (rest of your filtering and saving logic remains the same) ...
        initial_len = len(processed_dataset)
        processed_dataset = processed_dataset.filter(lambda x: x['text'] and len(x['text'].strip()) > 0)
        filtered_count = initial_len - len(processed_dataset)
        if filtered_count > 0:
            log_msg = f"Filtered out {filtered_count} empty or invalid examples."
            await send_log_via_ws(log_msg, progress=70)
            logger.info(f"Preprocessing: {log_msg}")


        if len(processed_dataset) == 0:
             raise ValueError("Preprocessing resulted in an empty dataset. Check format and input data.")

        final_msg = f"Preprocessing complete. Final dataset size: {len(processed_dataset)} examples."
        await send_log_via_ws(final_msg, progress=90)
        logger.info(f"Preprocessing: {final_msg}")

        save_file = output_path / "dataset.jsonl"
        processed_dataset.to_json(save_file, orient="records", lines=True)

        await send_completion(f"Dataset preprocessed and saved to: {save_file}")

    except FileNotFoundError as e:
         trace_exception(e)
         await send_error(f"Preprocessing failed: File not found - {e}")
    except ValueError as e: # Catch specific ValueErrors from our logic
         trace_exception(e)
         await send_error(f"Preprocessing failed: Invalid input, format, or configuration - {e}")
    except KeyError as e: # Catch KeyErrors from missing fields
        trace_exception(e)
        await send_error(f"Preprocessing failed: Missing data field - {e}")
    except Exception as e: # Catch all other unexpected errors
        trace_exception(e)
        await send_error(f"Dataset preprocessing failed unexpectedly: {e}")

async def run_fuse_datasets(req: FuseDatasetsRequest):
    try:
        await send_log_via_ws("Starting dataset fusion...", progress=0)
        logger.info("Starting dataset fusion.")
        output_path = _resolve_path(req.output_dataset_path)
        output_path.mkdir(parents=True, exist_ok=True)

        datasets_to_fuse = []

        for i, (source, path) in enumerate([
            (req.dataset1_source, req.dataset1_path),
            (req.dataset2_source, req.dataset2_path)
        ], 1):
            log_msg_load = f"Loading dataset {i} ({source}): {path}"
            await send_log_via_ws(log_msg_load)
            logger.info(f"Dataset Fusion: {log_msg_load}")
            if source == 'huggingface':
                ds = load_dataset(path, split='train')
            elif source == 'local':
                local_p = _resolve_path(path)
                if not local_p.exists(): raise FileNotFoundError(f"Dataset {i} not found: {local_p}")
                if local_p.is_dir():
                    ds = load_dataset(str(local_p), split='train')
                elif local_p.suffix == '.jsonl':
                     ds = load_dataset('json', data_files=str(local_p), split='train')
                else:
                    raise ValueError(f"Unsupported local dataset {i} format: {local_p}. Expecting directory or .jsonl")
            else:
                 raise ValueError(f"Invalid source for dataset {i}: {source}")

            if "text" not in ds.column_names:
                raise ValueError(f"Dataset {i} ('{path}') must have a 'text' column. Preprocess it first.")

            datasets_to_fuse.append(ds)
            log_msg_loaded = f"Loaded dataset {i} with {len(ds)} examples."
            await send_log_via_ws(log_msg_loaded, progress=i*25)
            logger.info(f"Dataset Fusion: {log_msg_loaded}")


        await send_log_via_ws("Concatenating datasets...", progress=60)
        logger.info("Dataset Fusion: Concatenating datasets.")
        fused_dataset = concatenate_datasets(datasets_to_fuse)

        final_msg = f"Fusion complete. Total examples: {len(fused_dataset)}"
        await send_log_via_ws(final_msg, progress=90)
        logger.info(f"Dataset Fusion: {final_msg}")

        save_file = output_path / "fused_dataset.jsonl"
        fused_dataset.to_json(save_file, orient="records", lines=True)

        await send_completion(f"Datasets fused and saved to: {save_file}")

    except FileNotFoundError as e:
         trace_exception(e)
         await send_error(f"Dataset fusion failed: File not found - {e}")
    except ValueError as e:
        trace_exception(e)
        await send_error(f"Dataset fusion failed: {e}")
    except Exception as e:
        trace_exception(e)
        await send_error(f"Dataset fusion failed unexpectedly: {e}")


# --- Training Callback with ascii_colors.ProgressBar Integration & Loss Reporting ---
class WebSocketLogCallback(TrainerCallback):
    def __init__(self, progress_bar: Optional[ASCIIProgressBar] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        self.global_step = 0
        self.max_steps = 0
        self.pbar = progress_bar
        self.loop = loop 
        self._last_logged_step = 0 

    def _send_log_threadsafe(self, message: str, progress: Optional[float] = None, is_error: bool = False, loss_data: Optional[Dict[str, Any]] = None):
        if not self.loop:
            (logger.error if is_error else logger.info)(f"(Callback, no loop for WS) {message}")
            return
        
        payload = {"log": message}
        if progress is not None:
            payload["progress"] = progress
        if is_error: 
            payload["error"] = message 
        if loss_data is not None: # Add loss data to the payload
            payload["loss_update"] = loss_data


        async def task():
            await broadcast_message(payload)
            if not is_error: # Log non-error callback messages server-side
                 logger.info(f"(Callback) {message}")
        
        asyncio.run_coroutine_threadsafe(task(), self.loop)

    def on_train_begin(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
        self.max_steps = state.max_steps
        self._last_logged_step = 0
        if self.pbar:
            self.pbar.total = self.max_steps
            self.pbar.set_description("Training Started")
            self.pbar.update(0) 
        self._send_log_threadsafe("Training started.", progress=0)

    def on_log(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, logs=None, **kwargs):
        self.global_step = state.global_step 
        loss_payload = None
        if logs: 
            console_log_parts = []
            if "loss" in logs: 
                console_log_parts.append(f"Loss: {logs['loss']:.4f}")
                loss_payload = {"step": self.global_step, "loss": float(logs['loss'])}
            if "learning_rate" in logs: console_log_parts.append(f"LR: {logs['learning_rate']:.2e}")
            if "epoch" in logs: console_log_parts.append(f"Epoch: {logs['epoch']:.2f}")
            
            ws_log_str = f"Step {self.global_step}/{self.max_steps}: {logs}"
            progress_val = (self.global_step / self.max_steps) * 100 if self.max_steps > 0 else 0
            
            if self.pbar:
                steps_to_update = self.global_step - self._last_logged_step
                if steps_to_update > 0:
                    self.pbar.update(steps_to_update)
                    self._last_logged_step = self.global_step
                
                pbar_desc = f"Training (Step {self.global_step}/{self.max_steps})"
                if console_log_parts:
                    pbar_desc += " | " + ", ".join(console_log_parts)
                self.pbar.set_description(pbar_desc)

            # Send log with potential loss data
            self._send_log_threadsafe(ws_log_str, progress=progress_val, loss_data=loss_payload)

    def on_epoch_begin(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
        epoch_num = int(state.epoch + 1) 
        num_epochs = int(state.num_train_epochs)
        msg = f"Epoch {epoch_num}/{num_epochs} starting..."
        if self.pbar:
            current_desc = self.pbar.desc.split(" | ")[0] 
            self.pbar.set_description(f"{current_desc} | {msg}")
        self._send_log_threadsafe(msg)

    def on_epoch_end(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
        epoch_num = int(state.epoch +1) 
        num_epochs = int(state.num_train_epochs)
        progress_val = (epoch_num / num_epochs) * 100 if num_epochs > 0 else 0
        msg = f"Epoch {epoch_num} completed."
        if self.pbar:
            current_desc = self.pbar.desc.split(" | ")[0]
            self.pbar.set_description(f"{current_desc} | {msg}")
        self._send_log_threadsafe(msg, progress=progress_val)

    def on_train_end(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs):
        if self.pbar:
            if self.pbar.total is not None and self.pbar.n < self.pbar.total:
                self.pbar.update(self.pbar.total - self.pbar.n)
            self.pbar.set_description("Training Finished")
            self.pbar.close() 
        self._send_log_threadsafe("Training process finished by Trainer.", progress=100)


async def run_train(req: TrainRequest):
    console_pbar: Optional[ASCIIProgressBar] = None
    global main_event_loop 

    try:
        await send_log_via_ws(f"Starting training job: {req.training_method} method.", progress=0)
        logger.info(f"Starting training job: {req.training_method} method for model {req.model_name}.")

        base_model_path = _resolve_path(req.model_name)
        output_dir = _resolve_path(req.output_model_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        dataset_path = _resolve_path(req.dataset_name)

        if req.gpu_ids and HAS_NVIDIA_GPU:
            os.environ["CUDA_VISIBLE_DEVICES"] = req.gpu_ids
            logger.info(f"Set CUDA_VISIBLE_DEVICES={req.gpu_ids}")
            torch.cuda.empty_cache() 
            try:
                pynvml.nvmlInit()
                num_gpus_visible = pynvml.nvmlDeviceGetCount()
                pynvml.nvmlShutdown()
                logger.info(f"Visible GPUs after setting env var: {num_gpus_visible}")
                if num_gpus_visible == 0 and req.gpu_ids:
                    raise ValueError(f"Specified GPU IDs '{req.gpu_ids}' not found or accessible.")
            except Exception as e:
                 logger.warning(f"Could not verify visible GPU count after setting CUDA_VISIBLE_DEVICES: {e}")
        
        await send_log_via_ws(f"Loading tokenizer for {base_model_path}...", progress=5)
        logger.info(f"Training: Loading tokenizer for {base_model_path}")
        tokenizer = AutoTokenizer.from_pretrained(str(base_model_path), trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info("Set tokenizer pad_token to eos_token")

        tokenizer.padding_side = "right" 
        logger.info("Set tokenizer.padding_side to 'right' for SFTTrainer compatibility.")            

        await send_log_via_ws(f"Loading dataset from {dataset_path} ({req.dataset_source})...", progress=10)
        logger.info(f"Training: Loading dataset from {dataset_path} ({req.dataset_source})")
        if req.dataset_source == 'huggingface':
            dataset = load_dataset(req.dataset_name, split="train")
        elif req.dataset_source == 'local':
             if not dataset_path.exists(): raise FileNotFoundError(f"Dataset path not found: {dataset_path}")
             if dataset_path.is_dir():
                 dataset = load_dataset(str(dataset_path), split="train")
             elif dataset_path.suffix == '.jsonl':
                  dataset = load_dataset('json', data_files=str(dataset_path), split="train")
             else:
                 raise ValueError("Local dataset must be a directory or a .jsonl file")
        else:
            raise ValueError("Invalid dataset source")

        if "text" not in dataset.column_names:
            raise ValueError("Dataset must contain a 'text' column. Please preprocess first.")
        
        log_ds_loaded = f"Loaded dataset with {len(dataset)} examples."
        await send_log_via_ws(log_ds_loaded, progress=15)
        logger.info(f"Training: {log_ds_loaded}")

        bnb_config = None
        if HAS_NVIDIA_GPU and torch.cuda.is_available() and req.training_method == 'lora': 
            pass
        elif not (HAS_NVIDIA_GPU and torch.cuda.is_available()):
            await send_log_via_ws("Warning: No GPU detected or PyTorch CUDA unavailable. Training will be very slow on CPU.", progress=18)
            logger.warning("Training: No GPU detected or PyTorch CUDA unavailable. CPU training.")

        fp16_enabled = req.fp16 and HAS_NVIDIA_GPU and torch.cuda.is_available()
        bf16_enabled = False 
        
        if fp16_enabled:
            logger.info("FP16 mixed precision training enabled.")
        
        model_dtype = torch.float32
        if bf16_enabled: 
            model_dtype = torch.bfloat16
            logger.info("Using bfloat16 for model.")
        elif fp16_enabled:
            model_dtype = torch.float16
            logger.info("Using float16 for model.")

        await send_log_via_ws(f"Loading base model: {base_model_path}...", progress=20)
        logger.info(f"Training: Loading base model {base_model_path} with dtype {model_dtype}")
        model = AutoModelForCausalLM.from_pretrained(
            str(base_model_path),
            quantization_config=bnb_config,
            device_map=get_device_map(),
            trust_remote_code=True,
            torch_dtype=model_dtype
        )
        model.config.use_cache = False

        if HAS_NVIDIA_GPU and torch.cuda.is_available() and req.training_method == 'lora':
             if bnb_config and (bnb_config.load_in_4bit or bnb_config.load_in_8bit):
                 await send_log_via_ws("Preparing model for k-bit training...", progress=25)
                 logger.info("Training: Preparing model for k-bit training.")
                 model = prepare_model_for_kbit_training(model)

        peft_config = None
        if req.training_method == 'lora':
            await send_log_via_ws("Configuring LoRA...", progress=30)
            logger.info("Training: Configuring LoRA.")
            target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
            peft_config = LoraConfig(
                r=req.lora_r,
                lora_alpha=req.lora_alpha,
                lora_dropout=req.lora_dropout,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=target_modules
            )
            logger.info(f"LoRA configured: r={req.lora_r}, alpha={req.lora_alpha}, dropout={req.lora_dropout}")

        await send_log_via_ws("Setting up training arguments...", progress=35)
        logger.info("Training: Setting up TrainingArguments.")
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            per_device_train_batch_size=req.per_device_train_batch_size,
            gradient_accumulation_steps=req.gradient_accumulation_steps,
            learning_rate=req.learning_rate,
            num_train_epochs=req.num_train_epochs,
            max_grad_norm=req.max_grad_norm,
            weight_decay=req.weight_decay,
            fp16=fp16_enabled, 
            bf16=bf16_enabled, 
            logging_steps=10, 
            save_strategy="epoch", 
            report_to="none", 
            optim="paged_adamw_8bit" if HAS_NVIDIA_GPU and bnb_config else "adamw_torch",
            disable_tqdm=True # Disable HuggingFace Trainer's default TQDM progress bar
        )

        if HAS_NVIDIA_GPU and torch.cuda.is_available(): 
             console_pbar = ASCIIProgressBar(
                 total=0, 
                 desc="Initializing Training",
                 unit="steps",
                 color=ASCIIColors.color_bright_cyan, 
                 bar_style="blocks" 
             )
        
        ws_callback = WebSocketLogCallback(progress_bar=console_pbar, loop=main_event_loop)

        await send_log_via_ws("Initializing Trainer...", progress=40)
        logger.info("Training: Initializing SFTTrainer.")
        trainer = SFTTrainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            tokenizer=tokenizer,
            dataset_text_field="text", 
            max_seq_length=req.max_seq_length,
            peft_config=peft_config if req.training_method == 'lora' else None,
            callbacks=[ws_callback], 
        )

        await send_log_via_ws("Starting training process...", progress=45)
        logger.info("Training: Calling trainer.train()...")
        train_result = await asyncio.to_thread(trainer.train) 
        logger.info(f"Training: trainer.train() finished. Result: {train_result}")

        await send_log_via_ws("Training finished. Saving final model/adapter...", progress=95)
        logger.info("Training: Saving final model/adapter.")
        await asyncio.to_thread(trainer.save_model, str(output_dir))
        tokenizer.save_pretrained(str(output_dir))

        del model
        del trainer
        if HAS_NVIDIA_GPU and torch.cuda.is_available():
            torch.cuda.empty_cache()

        await send_completion(f"Training complete. Model/Adapter saved to: {output_dir}")

    except FileNotFoundError as e:
        trace_exception(e) 
        if console_pbar: console_pbar.close()
        await send_error(f"Training failed: File not found - {e}")
    except ValueError as e:
        trace_exception(e)
        if console_pbar: console_pbar.close()
        await send_error(f"Training failed: Invalid input or configuration - {e}")
    except Exception as e:
        if console_pbar: console_pbar.close()
        # Use return_trace=True to get the string for the WS message
        trace_str = trace_exception(e, return_trace=True) 
        await send_error(f"Training failed unexpectedly: {e}\nTrace:\n{trace_str}")
    finally:
         if console_pbar: 
             console_pbar.close()
         if req.gpu_ids and "CUDA_VISIBLE_DEVICES" in os.environ:
             pass


async def run_fuse(req: FuseRequest):
    try:
        await send_log_via_ws(f"Starting LoRA fusion: merging {req.lora_model_path} into {req.base_model_path}", progress=0)
        logger.info(f"Fusing LoRA: {req.lora_model_path} into {req.base_model_path}")

        base_model_p = _resolve_path(req.base_model_path)
        lora_model_p = _resolve_path(req.lora_model_path)
        output_p = _resolve_path(req.output_path)
        output_p.mkdir(parents=True, exist_ok=True)

        dtype = torch.bfloat16 if HAS_NVIDIA_GPU and torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
        await send_log_via_ws(f"Loading base model ({base_model_p}) in {dtype}...", progress=10)
        logger.info(f"Fusion: Loading base model {base_model_p} in {dtype}")
        base_model = AutoModelForCausalLM.from_pretrained(
            str(base_model_p),
            torch_dtype=dtype,
            device_map=get_device_map(),
            trust_remote_code=True,
        )

        await send_log_via_ws(f"Loading LoRA adapter ({lora_model_p})...", progress=40)
        logger.info(f"Fusion: Loading LoRA adapter {lora_model_p}")
        merged_model = PeftModel.from_pretrained(
            base_model,
            str(lora_model_p),
            device_map=get_device_map()
        )

        await send_log_via_ws("Merging adapter layers...", progress=60)
        logger.info("Fusion: Merging adapter layers.")
        merged_model = await asyncio.to_thread(merged_model.merge_and_unload)
        await send_log_via_ws("Merge complete.", progress=80)
        logger.info("Fusion: Merge complete.")

        await send_log_via_ws(f"Saving fused model to {output_p}...", progress=90)
        logger.info(f"Fusion: Saving fused model to {output_p}")
        await asyncio.to_thread(merged_model.save_pretrained, str(output_p))

        tokenizer = AutoTokenizer.from_pretrained(str(base_model_p), trust_remote_code=True)
        tokenizer.save_pretrained(str(output_p))
        await send_log_via_ws("Tokenizer saved.", progress=95)
        logger.info("Fusion: Tokenizer saved.")

        del base_model
        del merged_model
        if HAS_NVIDIA_GPU and torch.cuda.is_available():
            torch.cuda.empty_cache()

        await send_completion(f"Model fusion complete. Fused model saved to: {output_p}")

    except Exception as e:
         trace_str = trace_exception(e, return_trace=True)
         await send_error(f"Model fusion failed: {e}\nTrace:\n{trace_str}")

async def run_query(req: QueryRequest) -> Dict[str, str]:
    output_text = "Error: Query execution failed."
    model = None # Ensure model is defined for potential cleanup in except block
    try:
        logger.info(f"Starting query for model: {req.model_path}")
        model_p = _resolve_path(req.model_path)

        dtype = torch.bfloat16 if HAS_NVIDIA_GPU and torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
        logger.info(f"Query: Loading model {model_p} in {dtype}...")
        model = AutoModelForCausalLM.from_pretrained(
            str(model_p),
            torch_dtype=dtype,
            device_map=get_device_map(),
            trust_remote_code=True,
        )
        model.eval() 

        tokenizer = AutoTokenizer.from_pretrained(str(model_p), trust_remote_code=True)
        if tokenizer.pad_token is None:
             tokenizer.pad_token_id = tokenizer.eos_token_id # More robust for generation
             logger.info("Set tokenizer pad_token_id to eos_token_id for query.")


        # --- Prepare Input with Chat Template if available ---
        if tokenizer.chat_template:
            logger.info("Query: Applying chat template.")
            # Assume the input_text is a single user turn for simplicity
            messages = [{"role": "user", "content": req.input_text}]
            try:
                prompt_from_template = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                logger.debug(f"Prompt from template: {prompt_from_template}")
                inputs = tokenizer(prompt_from_template, return_tensors="pt").to(model.device)
            except Exception as e_template:
                logger.warning(f"Failed to apply chat template: {e_template}. Falling back to direct tokenization.")
                trace_exception(e_template)
                inputs = tokenizer(req.input_text, return_tensors="pt").to(model.device)
        else:
            logger.info("Query: No chat template found. Using direct tokenization.")
            inputs = tokenizer(req.input_text, return_tensors="pt").to(model.device)
        # --- End Input Preparation ---


        logger.info("Query: Generating response...")
        # Ensure pad_token_id is correctly set for generation config
        # Some models might not have it, and eos_token_id is a common fallback.
        pad_token_id_for_gen = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id

        generation_config = GenerationConfig(
            max_new_tokens=req.max_new_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
            do_sample=True, 
            pad_token_id=pad_token_id_for_gen, # Use the determined pad_token_id
            eos_token_id=tokenizer.eos_token_id # EOS token ID should always be available
        )

        with torch.no_grad(): 
             outputs = await asyncio.to_thread(
                 model.generate,
                 input_ids=inputs.input_ids, # Pass input_ids directly
                 attention_mask=inputs.attention_mask, # Pass attention_mask
                 generation_config=generation_config
             )

        # --- Decode Output ---
        # Slice output to get only the newly generated tokens
        # The length of the input_ids might differ if a template was applied
        input_ids_length = inputs.input_ids.shape[1]
        output_tokens = outputs[0][input_ids_length:]
        output_text = tokenizer.decode(output_tokens, skip_special_tokens=True)

        logger.info("Query: Completed successfully.")
        del model 
        if HAS_NVIDIA_GPU and torch.cuda.is_available():
             torch.cuda.empty_cache()

        return {"output_text": output_text.strip()}

    except Exception as e:
        trace_str = trace_exception(e, return_trace=True)
        logger.error(f"Query failed: {e}\nTrace:\n{trace_str}") # Log full trace server-side
        if model is not None: 
            del model 
        if HAS_NVIDIA_GPU and torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {"output_text": f"Error during generation: {e}"} # Send simpler error to client


async def run_quantize(req: QuantizeRequest):
    model = None 
    try:
        await send_log_via_ws(f"Starting quantization: Tool='{req.quantization_tool}', Method='{req.quantization_method}'", progress=0)
        logger.info(f"Quantization: Tool='{req.quantization_tool}', Method='{req.quantization_method}' for model {req.model_path}")
        model_p = _resolve_path(req.model_path)
        output_p = _resolve_path(req.output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True) 

        if not model_p.exists():
            raise FileNotFoundError(f"Input model path not found: {model_p}")

        if req.quantization_tool == 'bitsandbytes':
             await send_log_via_ws("Using BitsAndBytes: Loading model with quantization config...", progress=10)
             logger.info("Quantization: Using BitsAndBytes.")
             bnb_config_quant = None
             if req.quantization_method == 'load_in_8bit':
                 bnb_config_quant = BitsAndBytesConfig(load_in_8bit=True)
             elif req.quantization_method == 'load_in_4bit':
                 bnb_config_quant = BitsAndBytesConfig(
                     load_in_4bit=True,
                     bnb_4bit_quant_type="nf4", 
                     bnb_4bit_compute_dtype=torch.bfloat16 if HAS_NVIDIA_GPU and torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16,
                     bnb_4bit_use_double_quant=True,
                 )
             else:
                 raise ValueError(f"Unsupported BitsAndBytes method: {req.quantization_method}")

             if not (HAS_NVIDIA_GPU and torch.cuda.is_available()): 
                 raise RuntimeError("BitsAndBytes quantization requires an NVIDIA GPU and CUDA.")

             model = AutoModelForCausalLM.from_pretrained(
                 str(model_p),
                 quantization_config=bnb_config_quant,
                 device_map="cpu",
                 trust_remote_code=True,
             )
             await send_log_via_ws("Model loaded. Saving quantized model config...", progress=70)
             logger.info("Quantization: Model loaded with BnB config, saving...")
             await asyncio.to_thread(model.save_pretrained, str(output_p))

             tokenizer = AutoTokenizer.from_pretrained(str(model_p), trust_remote_code=True)
             tokenizer.save_pretrained(str(output_p))
             await send_log_via_ws("Tokenizer saved.", progress=95)
             logger.info("Quantization: Tokenizer saved.")

             del model
             if HAS_NVIDIA_GPU and torch.cuda.is_available():
                torch.cuda.empty_cache()

             await send_completion(f"BitsAndBytes model config saved to: {output_p}. Note: Requires BitsAndBytes on load.")


        elif req.quantization_tool == 'gguf':
             await send_log_via_ws("Using GGUF: Attempting conversion via llama.cpp script.", progress=10)
             await send_log_via_ws("Warning: This requires 'llama.cpp' to be cloned and built locally.", progress=15)
             logger.info("Quantization: Using GGUF via llama.cpp.")

             llama_cpp_dir = Path(os.getenv("LLAMA_CPP_DIR", "../llama.cpp")).resolve() 
             convert_script = llama_cpp_dir / "convert.py" 
             quantize_binary = llama_cpp_dir / "quantize" 

             alt_convert_script = llama_cpp_dir / "convert-hf-to-gguf.py"
             if not convert_script.exists() and alt_convert_script.exists():
                 convert_script = alt_convert_script
                 logger.info(f"Using convert script: {convert_script}")


             if not convert_script.exists():
                 raise FileNotFoundError(f"llama.cpp convert script (convert.py or convert-hf-to-gguf.py) not found at: {llama_cpp_dir}. Set LLAMA_CPP_DIR env var or adjust path.")
             if not quantize_binary.exists():
                 raise FileNotFoundError(f"llama.cpp quantize binary not found at: {quantize_binary}. Build llama.cpp first (run 'make').")

             fp16_gguf_path = output_p.parent / f"{output_p.stem}_fp16.gguf"
             convert_cmd = [
                 sys.executable, 
                 str(convert_script),
                 str(model_p), 
                 "--outfile", str(fp16_gguf_path),
                 "--outtype", "f16" 
             ]
             log_convert_cmd = f"Running conversion to FP16 GGUF: {' '.join(convert_cmd)}"
             await send_log_via_ws(log_convert_cmd, progress=30)
             logger.info(f"Quantization: {log_convert_cmd}")


             process = await asyncio.create_subprocess_exec(
                 *convert_cmd,
                 stdout=asyncio.subprocess.PIPE,
                 stderr=asyncio.subprocess.PIPE
             )
             stdout, stderr = await process.communicate()

             if process.returncode != 0:
                 error_msg = stderr.decode(errors='ignore').strip() if stderr else stdout.decode(errors='ignore').strip()
                 await send_log_via_ws(f"FP16 GGUF conversion stdout: {stdout.decode(errors='ignore')}") # Removed is_error for plain log
                 await send_log_via_ws(f"FP16 GGUF conversion stderr: {stderr.decode(errors='ignore')}")
                 raise RuntimeError(f"GGUF FP16 conversion failed: {error_msg}")
             else:
                  await send_log_via_ws("FP16 GGUF conversion successful.", progress=60)
                  logger.info("Quantization: FP16 GGUF conversion successful.")
                  log_output = stdout.decode(errors='ignore').strip()
                  if log_output: 
                      await send_log_via_ws(f"Conversion Output:\n{log_output}")
                      logger.debug(f"GGUF Conversion Output:\n{log_output}")


             quantize_cmd = [
                 str(quantize_binary),
                 str(fp16_gguf_path), 
                 str(output_p),     
                 req.quantization_method 
             ]
             log_quant_cmd = f"Running quantization to {req.quantization_method}: {' '.join(quantize_cmd)}"
             await send_log_via_ws(log_quant_cmd, progress=70)
             logger.info(f"Quantization: {log_quant_cmd}")

             process = await asyncio.create_subprocess_exec(
                 *quantize_cmd,
                 stdout=asyncio.subprocess.PIPE,
                 stderr=asyncio.subprocess.PIPE
             )
             stdout, stderr = await process.communicate()

             if process.returncode != 0:
                 error_msg = stderr.decode(errors='ignore').strip() if stderr else stdout.decode(errors='ignore').strip()
                 await send_log_via_ws(f"GGUF quant stdout: {stdout.decode(errors='ignore')}")
                 await send_log_via_ws(f"GGUF quant stderr: {stderr.decode(errors='ignore')}")
                 raise RuntimeError(f"GGUF quantization to {req.quantization_method} failed: {error_msg}")
             else:
                  await send_log_via_ws(f"GGUF quantization to {req.quantization_method} successful.", progress=95)
                  logger.info(f"Quantization: GGUF quantization to {req.quantization_method} successful.")
                  log_output = stdout.decode(errors='ignore').strip()
                  if log_output: 
                      await send_log_via_ws(f"Quantization Output:\n{log_output}")
                      logger.debug(f"GGUF Quantization Output:\n{log_output}")


             try:
                 fp16_gguf_path.unlink()
                 await send_log_via_ws("Cleaned up intermediate FP16 GGUF file.")
                 logger.info("Quantization: Cleaned up intermediate FP16 GGUF file.")
             except OSError as e_unlink:
                 await send_log_via_ws(f"Warning: Could not delete intermediate file {fp16_gguf_path}: {e_unlink}")
                 logger.warning(f"Quantization: Could not delete intermediate file {fp16_gguf_path}: {e_unlink}")


             await send_completion(f"GGUF quantization complete. Model saved to: {output_p}")
        else:
            raise ValueError(f"Unknown quantization tool: {req.quantization_tool}")

    except FileNotFoundError as e:
         trace_exception(e)
         await send_error(f"Quantization failed: File not found - {e}")
    except ValueError as e:
        trace_exception(e)
        await send_error(f"Quantization failed: Invalid input - {e}")
    except RuntimeError as e: 
        trace_exception(e)
        await send_error(f"Quantization failed: Runtime error - {e}")
    except Exception as e:
        if model is not None: del model 
        trace_str = trace_exception(e, return_trace=True)
        await send_error(f"Quantization failed unexpectedly: {e}\nTrace:\n{trace_str}")


async def run_push_to_hf(req: PushToHFRequest):
    try:
        await send_log_via_ws(f"Starting push to Hugging Face Hub: {req.hf_repo_name}", progress=0)
        logger.info(f"Push to HF: Starting for repo {req.hf_repo_name}, local path {req.local_model_path}")
        local_path = _resolve_path(req.local_model_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local model path not found: {local_path}")

        repo_id = f"{req.hf_username}/{req.hf_repo_name}" if req.hf_username else req.hf_repo_name
        await send_log_via_ws(f"Target repository: {repo_id}", progress=10)
        logger.info(f"Push to HF: Target repository {repo_id}")

        api = HfApi(token=req.hf_token)

        try:
            repo_url = await asyncio.to_thread(
                api.create_repo,
                repo_id=repo_id, 
                private=req.private_repo, 
                exist_ok=True
            )
            await send_log_via_ws(f"Repository ensured: {repo_url} (Private: {req.private_repo})", progress=30)
            logger.info(f"Push to HF: Repository ensured at {repo_url}")
        except Exception as e_repo:
             await send_log_via_ws(f"Warning: Could not explicitly create/verify repo (permission issue or invalid name?). Upload will attempt anyway. Error: {e_repo}", progress=30)
             logger.warning(f"Push to HF: Could not explicitly create/verify repo {repo_id}. Error: {e_repo}")


        await send_log_via_ws(f"Uploading {'folder' if local_path.is_dir() else 'file'} {local_path}...", progress=40)
        logger.info(f"Push to HF: Uploading {'folder' if local_path.is_dir() else 'file'} {local_path}")

        if local_path.is_dir():
            await asyncio.to_thread(
                api.upload_folder,
                folder_path=str(local_path),
                repo_id=repo_id,
                repo_type="model",
                commit_message=req.commit_message,
            )
        elif local_path.is_file():
             await asyncio.to_thread(
                 api.upload_file,
                 path_or_fileobj=str(local_path),
                 path_in_repo=local_path.name, 
                 repo_id=repo_id,
                 repo_type="model",
                 commit_message=req.commit_message,
             )
        else:
             raise ValueError(f"Invalid local path type: {local_path}")

        await send_completion(f"Successfully pushed model to Hugging Face Hub: https://huggingface.co/{repo_id}")

    except FileNotFoundError as e:
         trace_exception(e)
         await send_error(f"Push to HF failed: File not found - {e}")
    except ValueError as e: 
        trace_exception(e)
        await send_error(f"Push to HF failed: Invalid input - {e}")
    except Exception as e: 
         trace_str = trace_exception(e, return_trace=True)
         error_str = str(e).replace(req.hf_token, "***TOKEN***") 
         await send_error(f"Push to HF failed: {error_str}\nTrace:\n{trace_str}")


# --- API Endpoints (remain unchanged) ---

@app.post("/download_model/", status_code=202)
async def download_model_endpoint(req: DownloadModelRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_download_model, req)
    return {"message": "Model download task started."}

@app.post("/preprocess/", status_code=202)
async def preprocess_dataset_endpoint(req: PreprocessDatasetRequest, background_tasks: BackgroundTasks):
     background_tasks.add_task(run_preprocess_dataset, req)
     return {"message": "Dataset preprocessing task started."}

@app.post("/fuse_datasets/", status_code=202)
async def fuse_datasets_endpoint(req: FuseDatasetsRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_fuse_datasets, req)
    return {"message": "Dataset fusion task started."}


@app.post("/train/", status_code=202)
async def train_endpoint(req: TrainRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_train, req)
    return {"message": "Training task started."}

@app.post("/fuse/", status_code=202)
async def fuse_endpoint(req: FuseRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_fuse, req)
    return {"message": "Model fusion task started."}

@app.post("/query/")
async def query_endpoint(req: QueryRequest):
    result = await run_query(req)
    if "Error" in result.get("output_text", ""):
         return JSONResponse(content={"detail": result["output_text"]}, status_code=500)
    return result


@app.post("/quantize/", status_code=202)
async def quantize_endpoint(req: QuantizeRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_quantize, req)
    return {"message": "Quantization task started."}

@app.post("/push_to_hf/", status_code=202)
async def push_to_hf_endpoint(req: PushToHFRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_push_to_hf, req)
    return {"message": "Push to Hugging Face Hub task started."}


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Finetuning App Backend Server")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()

    # Using logger.info for standard logging, ascii_colors.print for direct console output if needed
    logger.info(f"Starting server on {ASCIIColors.yellow(args.host)}:{ASCIIColors.yellow(str(args.port))}")


    if os.getenv("LLAMA_CPP_DIR"):
         logger.info(f"Using LLAMA_CPP_DIR: {ASCIIColors.cyan(os.getenv('LLAMA_CPP_DIR'))}")
    else:
         logger.warning(f"{ASCIIColors.color_yellow}LLAMA_CPP_DIR environment variable not set. GGUF quantization will fail if llama.cpp is not found at '../llama.cpp' (relative to server.py).{ASCIIColors.color_reset}")

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
