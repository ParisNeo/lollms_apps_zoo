import base64
import io
import matplotlib.pyplot as plt
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

class PlotRequest(BaseModel):
    code: str

def read_image_file():
    try:
        with open('output.png', 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading image file: {str(e)}")
    
@app.post("/generate_plot")
async def generate_plot(request: PlotRequest):
    try:
        # Execute the generated code
        exec(request.code)

        # Encode the image as base64
        img_base64 = read_image_file()

        # Close the plot to free up memory
        plt.close()

        return {"image": img_base64}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)