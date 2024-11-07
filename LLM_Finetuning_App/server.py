from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
import pipmaster as pm
import json

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
            dataset = datasets.load_from_disk(config.dataset_name)
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
            output_dir="./results",
            learning_rate=config.learning_rate,
            num_train_epochs=config.num_train_epochs,
            per_device_train_batch_size=config.per_device_train_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            max_grad_norm=config.max_grad_norm,
            weight_decay=config.weight_decay,
        )

        # Prepare the trainer
        trainer = trl.SFTTrainer(
            model=model,
            train_dataset=tokenized_dataset["train"],
            peft_config=peft_config,
            dataset_text_field="text",
            args=training_args,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)