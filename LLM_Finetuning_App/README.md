# LLM Finetuning App Documentation

## Overview

The LLM Finetuning App is a web-based application for fine-tuning, fusing, and quantizing Large Language Models (LLMs). It provides a user-friendly interface for various operations related to LLM training and optimization.

## Features

1. Download Model
2. Train Model
3. Fuse Model
4. Quantize Model

## User Interface

The app consists of four main sections, each accessible via buttons at the top of the page:

- Download Model
- Train
- Fuse
- Quantize

## Functionality

### 1. Download Model

This section allows users to download a model from Hugging Face.

Fields:
- Model Name (Hugging Face path)
- Target Directory

### 2. Train Model

This section provides options for fine-tuning a model.

Fields:
- Model Name (Hugging Face path)
- Dataset Source (Hugging Face or Local)
- Dataset Name/Path
- Dataset Format (Single Text, Instruction-Input-Output, Question-Answer, Custom)
- Custom Format (if Custom dataset format is selected)
- Output Model Path
- Learning Rate
- Number of Epochs
- Batch Size
- Gradient Accumulation Steps
- Max Gradient Norm
- Weight Decay
- LoRA Alpha
- LoRA Dropout
- LoRA R
- Max Sequence Length
- GPU IDs
- Max Memory per GPU
- Max CPU Memory
- Enable FP16 (Mixed Precision)

### 3. Fuse Model

This section allows users to fuse a base model with a LoRA model.

Fields:
- Base Model Path
- LoRA Model Path
- Fused Output Path

### 4. Quantize Model

This section provides options for quantizing a model.

Fields:
- Model Path
- Quantized Output Path
- Quantization Bits (8-bit or 4-bit)

## Progress Tracking

The app displays a progress bar and log output for ongoing operations.

## Internationalization

The app supports multiple languages. Currently, English and French are available. Users can switch between languages using a dropdown menu in the top-right corner.

## Technical Details

- The app uses WebSocket for real-time progress updates.
- Form submissions are handled asynchronously using fetch API.
- The UI is built with HTML and styled using Tailwind CSS.
- Internationalization is implemented using a custom WebAppLocalizer class.

## Error Handling

The app provides error alerts for failed operations and logs errors to the console for debugging purposes.