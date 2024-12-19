import os
from typing import List

import sympy as sp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DerivativeRequest(BaseModel):
    function: str
    parameters: List[str]


class DerivativeResponse(BaseModel):
    derivatives: List[str]


@app.post("/generate_derivatives", response_model=DerivativeResponse)
async def generate_derivatives(request: DerivativeRequest):
    try:
        # Parse the function and parameters
        expr = sp.sympify(request.function)
        params = [sp.Symbol(param) for param in request.parameters]

        # Generate partial derivatives
        derivatives = []
        for param in params:
            derivative = sp.diff(expr, param)
            func_str = f"def derivative_{param}({', '.join(request.parameters)}):\n    return {derivative}"
            derivatives.append(func_str)

        return DerivativeResponse(derivatives=derivatives)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
