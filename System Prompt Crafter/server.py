import os
from dotenv import load_dotenv
from lollms_client import LollmsClient, LollmsXTTS, LollmsClipper, GenerationPresets, MSG_TYPE, LollmsMP3Player, LollmsText2Audio, ASCIIColors
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json

# Load environment variables
load_dotenv()
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Lollms Client Configuration ---
try:
    LOLLMS_HOST = os.getenv("LOLLMS_HOST", "http://localhost:9642")
    LOLLMS_KEY = os.getenv("LOLLMS_KEY", "")
    VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() == "true"
    CRAFTOR_MODEL_NAME = os.getenv("CRAFTOR_MODEL_NAME")
    TESTER_MODEL_NAME = os.getenv("TESTER_MODEL_NAME")

    if not VERIFY_SSL:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        ASCIIColors.warning("SSL certificate verification is disabled.")

    base_llm_binding_config = {
        "host_address": LOLLMS_HOST,
        "service_key": LOLLMS_KEY,
        "verify_ssl_certificate": VERIFY_SSL
    }

    # Client for Crafting/Analysis
    craftor_config = base_llm_binding_config.copy()
    if CRAFTOR_MODEL_NAME and CRAFTOR_MODEL_NAME.strip() != "":
        craftor_config["model_name"] = CRAFTOR_MODEL_NAME
        ASCIIColors.info(f"Craftor configured to use model: {CRAFTOR_MODEL_NAME}")
    
    craftor_lc = LollmsClient(
        llm_binding_name="lollms",
        llm_binding_config=craftor_config,
        force_new=True
    )

    # Client for Testing
    tester_config = base_llm_binding_config.copy()
    if TESTER_MODEL_NAME and TESTER_MODEL_NAME.strip() != "":
        tester_config["model_name"] = TESTER_MODEL_NAME
        ASCIIColors.info(f"Tester configured to use model: {TESTER_MODEL_NAME}")

    tester_lc = LollmsClient(
        llm_binding_name="lollms",
        llm_binding_config=tester_config,
        force_new=True
    )

    ASCIIColors.green("Successfully connected to Lollms service for both Craftor and Tester.")

except Exception as e:
    ASCIIColors.error(f"Failed to initialize LollmsClient: {e}")
    craftor_lc = None
    tester_lc = None

# --- Pydantic Models ---
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


# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("templates/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/api/v1/list_models")
def get_models_list():
    if not craftor_lc:
        raise HTTPException(status_code=503, detail="Lollms client not initialized.")
    try:
        return craftor_lc.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/start_crafting")
def start_crafting(request: CraftRequest):
    if not craftor_lc:
        raise HTTPException(status_code=503, detail="Craftor Lollms client not initialized.")

    meta_prompt = f"""
    You are an expert System Prompt Designer. Your task is to take a user's idea and generate a high-quality, robust system prompt.
    You must also generate a set of diverse user prompts to test for ADHERENCE to the system prompt's instructions.
    
    User's Idea: "{request.idea}"
    
    Based on this idea, provide a JSON object with the following structure:
    {{
      "system_prompt": "The detailed system prompt you designed.",
      "test_prompts": [
        "A first user prompt to test adherence.",
        "A second, different user prompt.",
        "A third prompt that tests a specific constraint or edge case.",
        "A fourth prompt that tempts the AI to break a rule.",
        "A fifth general prompt to check overall compliance."
      ],
      "judging_criteria": "A brief explanation of what to look for in the test results to verify the AI is adhering to the system prompt."
    }}
    """
    try:
        response = craftor_lc.generate_text_with_structured_output(
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
    if not craftor_lc:
        raise HTTPException(status_code=503, detail="Craftor Lollms client not initialized.")

    test_results_str = json.dumps([res.dict() for res in request.test_results], indent=2)

    meta_prompt = f"""
    You are a System Prompt Adherence Analyst. Your goal is to determine if an AI has followed a given system prompt based on a series of tests. Your focus is SOLELY on adherence to instructions, not the quality or factual accuracy of the content.

    Current System Prompt:
    ---
    {request.system_prompt}
    ---

    Test Results:
    ---
    {test_results_str}
    ---

    Analyze the test results. Did the AI perfectly adhere to ALL instructions in the system prompt?
    - If YES, respond with a JSON object where `status` is 'success'.
    - If NO, identify the specific failures in adherence and create a refined system prompt that addresses these issues. Also, generate a new set of test prompts for the refined version. Respond with a JSON object where `status` is 'refine'.

    Provide your response as a JSON object with one of the following structures:

    Success case:
    {{
      "status": "success",
      "analysis": "A brief summary of why the prompt is considered successful.",
      "final_prompt": "{request.system_prompt}"
    }}

    Refinement case:
    {{
      "status": "refine",
      "analysis": "A detailed explanation of which rules were broken and why the prompt needs refinement.",
      "refined_prompt": "The new, improved system prompt.",
      "new_test_prompts": ["A new set of user prompts to test the refined system prompt."]
    }}
    """
    try:
        response = craftor_lc.generate_text_with_structured_output(
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
