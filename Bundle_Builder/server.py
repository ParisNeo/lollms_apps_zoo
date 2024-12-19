import asyncio
from typing import List

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class BundleRequest(BaseModel):
    name: str
    links: List[str]


class BundleResponse(BaseModel):
    js_bundle: str
    css_bundle: str


@app.post("/generate_bundle", response_model=BundleResponse)
async def generate_bundle(request: BundleRequest):
    js_content = []
    css_content = []

    async with httpx.AsyncClient() as client:
        tasks = [client.get(link) for link in request.links]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for link, response in zip(request.links, responses):
        if isinstance(response, Exception):
            print(f"Error fetching {link}: {str(response)}")
            continue

        if response.status_code != 200:
            print(f"Error fetching {link}: Status code {response.status_code}")
            continue

        content = response.text
        if link.endswith(".js"):
            js_content.append(f"// Source: {link}\n{content}\n")
        elif link.endswith(".css"):
            css_content.append(f"/* Source: {link} */\n{content}\n")
        else:
            print(f"Unsupported file type: {link}")

    js_bundle = "\n".join(js_content)
    css_bundle = "\n".join(css_content)

    return BundleResponse(js_bundle=js_bundle, css_bundle=css_bundle)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
