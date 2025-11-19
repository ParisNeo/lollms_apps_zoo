import os
from dotenv import load_dotenv
from lollms_client import LollmsClient
from ascii_colors import ASCIIColors
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import traceback
import argparse

load_dotenv()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def initialize_lollms_clients():
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.yellow("INITIALIZING LOLLMS CLIENTS")
    ASCIIColors.yellow("=" * 60)
    try:
        LOLLMS_HOST = os.getenv("LOLLMS_HOST", "http://localhost:9642")
        LOLLMS_KEY = os.getenv("LOLLMS_KEY", "")
        VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
        CRAFTOR_MODEL_NAME = os.getenv("CRAFTOR_MODEL_NAME")
        TESTER_MODEL_NAME = os.getenv("TESTER_MODEL_NAME")
        ASCIIColors.info(f"📡 LOLLMS_HOST: {LOLLMS_HOST}")
        ASCIIColors.info(f"🔑 LOLLMS_KEY: {'***' if LOLLMS_KEY else '(empty)'}")
        ASCIIColors.info(f"🔒 VERIFY_SSL: {VERIFY_SSL}")
        ASCIIColors.info(f"🎨 CRAFTOR_MODEL_NAME: {CRAFTOR_MODEL_NAME or '(not set - will use server default)'}")
        ASCIIColors.info(f"🧪 TESTER_MODEL_NAME: {TESTER_MODEL_NAME or '(not set - will use server default)'}")
        if not VERIFY_SSL:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            ASCIIColors.warning("⚠️  SSL certificate verification is disabled.")
        base_llm_binding_config = {
            "host_address": LOLLMS_HOST,
            "service_key": LOLLMS_KEY,
            "verify_ssl_certificate": VERIFY_SSL
        }
        ASCIIColors.info(f"📋 Base config: {json.dumps(base_llm_binding_config, indent=2)}")
        ASCIIColors.cyan("🎨 Initializing Craftor Client...")
        craftor_config = base_llm_binding_config.copy()
        if CRAFTOR_MODEL_NAME and CRAFTOR_MODEL_NAME.strip() != "":
            craftor_config["model_name"] = CRAFTOR_MODEL_NAME
            ASCIIColors.info(f"  ✓ Craftor configured to use model: {CRAFTOR_MODEL_NAME}")
        craftor_lc = LollmsClient(llm_binding_name="lollms", llm_binding_config=craftor_config, force_new=True)
        ASCIIColors.green("  ✅ Craftor client initialized successfully")
        ASCIIColors.cyan("🧪 Initializing Tester Client...")
        tester_config = base_llm_binding_config.copy()
        if TESTER_MODEL_NAME and TESTER_MODEL_NAME.strip() != "":
            tester_config["model_name"] = TESTER_MODEL_NAME
            ASCIIColors.info(f"  ✓ Tester configured to use model: {TESTER_MODEL_NAME}")
        tester_lc = LollmsClient(llm_binding_name="lollms", llm_binding_config=tester_config, force_new=True)
        ASCIIColors.green("  ✅ Tester client initialized successfully")
        ASCIIColors.green("=" * 60)
        ASCIIColors.green("✅ ALL CLIENTS INITIALIZED SUCCESSFULLY")
        ASCIIColors.green("=" * 60)
        return craftor_lc, tester_lc
    except Exception as e:
        ASCIIColors.error("=" * 60)
        ASCIIColors.error("❌ FAILED TO INITIALIZE LOLLMS CLIENTS")
        ASCIIColors.error("=" * 60)
        ASCIIColors.error(f"Error type: {type(e).__name__}")
        ASCIIColors.error(f"Error message: {str(e)}")
        ASCIIColors.error(f"Traceback:\n{traceback.format_exc()}")
        return None, None

craftor_lc, tester_lc = initialize_lollms_clients()

class CraftRequest(BaseModel):
    idea: str

class TestRequest(BaseModel):
    system_prompt: str
    test_prompts: List[str]

class TestResult(BaseModel):
    user_prompt: str
    ai_response: str

class RefineRequest(BaseModel):
    system_prompt: str
    test_results: List[TestResult]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    ASCIIColors.info("📄 Serving index.html")
    try:
        with open("templates/index.html") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except Exception as e:
        ASCIIColors.error(f"❌ Failed to read index.html: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load page: {str(e)}")

@app.get("/api/v1/list_models")
def get_models_list():
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.info("📡 API: /api/v1/list_models - Request received")
    ASCIIColors.yellow("=" * 60)
    if not craftor_lc:
        raise HTTPException(status_code=503, detail="Lollms client not initialized.")
    try:
        models = craftor_lc.list_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/start_crafting")
def start_crafting(request: CraftRequest):
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.info("🎨 API: /api/v1/start_crafting - Request received")
    ASCIIColors.yellow("=" * 60)
    if not craftor_lc:
        raise HTTPException(status_code=503, detail="Craftor Lollms client not initialized.")
    meta_prompt = f"""
    You are an expert System Prompt Designer. Your task is to take a user's idea and generate a high-quality, robust system prompt.
    You must also generate a set of diverse user prompts to test for ADHERENCE to the system prompt's instructions.
    User's Idea: "{request.idea}"
    Provide a JSON object with system prompt, test prompts, and judging criteria.
    """
    try:
        response = craftor_lc.generate_structured_content(
            prompt=meta_prompt,
            schema={
                "type": "object",
                "properties": {
                    "system_prompt": {"type": "string"},
                    "test_prompts": {"type": "array", "items": {"type": "string"}},
                    "judging_criteria": {"type": "string"}
                },
                "required": ["system_prompt", "test_prompts", "judging_criteria"]
            }
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate initial prompt: {e}")

@app.post("/api/v1/run_test")
def run_test(request: TestRequest):
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.info("🧪 API: /api/v1/run_test - Request received")
    ASCIIColors.yellow("=" * 60)
    if not tester_lc:
        raise HTTPException(status_code=503, detail="Tester Lollms client not initialized.")
    results = []
    for user_prompt in request.test_prompts:
        try:
            response = tester_lc.generate_text(
                prompt=user_prompt,
                system_prompt=request.system_prompt,
                max_generation_size=512
            )
            results.append({"user_prompt": user_prompt, "ai_response": response})
        except Exception as e:
            results.append({"user_prompt": user_prompt, "ai_response": f"Error during generation: {e}"})
    return results

@app.post("/api/v1/analyze_and_refine")
def analyze_and_refine(request: RefineRequest):
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.info("🔬 API: /api/v1/analyze_and_refine - Request received")
    ASCIIColors.yellow("=" * 60)
    if not craftor_lc:
        raise HTTPException(status_code=503, detail="Craftor Lollms client not initialized.")
    test_results_str = json.dumps([res.dict() for res in request.test_results], indent=2)
    meta_prompt = f"""
    You are a System Prompt Adherence Analyst. Evaluate adherence.
    System prompt:
    {request.system_prompt}
    Test results:
    {test_results_str}
    """
    try:
        response = craftor_lc.generate_structured_content(
            prompt=meta_prompt,
            schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success", "refine"]},
                    "analysis": {"type": "string"},
                    "final_prompt": {"type": "string"},
                    "refined_prompt": {"type": "string"},
                    "new_test_prompts": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["status", "analysis"]
            }
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze and refine prompt: {e}")

@app.on_event("startup")
async def startup_event():
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.green("🚀 APPLICATION STARTUP")
    ASCIIColors.yellow("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    ASCIIColors.yellow("=" * 60)
    ASCIIColors.info("🛑 APPLICATION SHUTDOWN")
    ASCIIColors.yellow("=" * 60)

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=9601)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
