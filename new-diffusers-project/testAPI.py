from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import StableDiffusionPipeline
import base64
from io import BytesIO
import asyncio

app = FastAPI()
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Svelte 개발 서버 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


model_id = "runwayml/stable-diffusion-v1-5" 

# Linaqruf/anything-v3.0
# runwayml/stable-diffusion-v1-5

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"using device: {device}")

pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float32,  # MPS에서는 float32가 더 안정적
    safety_checker=None
)

pipe = pipe.to(device)
pipe.enable_attention_slicing()
pipe.enable_vae_tiling()

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_inference_steps: int = 20
    guidance_scale: float = 7.5


current_progress = 0
def progress_callback(step: int, timestep: int, latents: torch.FloatTensor):
    global current_progress
    current_progress = int((step +1)/ pipe.config.num_inference_steps * 100)

@app.websocket("/ws/progress")
async def progress_websocket(websocket: WebSocket):
    await websocket.accept()
    global current_progress
    try:
        while True:
            await websocket.send_json({"progress": current_progress})
            await asyncio.sleep(0.1)
            if current_progress >= 100:
                break
    except Exception:
        pass
    finally:
        current_progress = 0

@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    global current_progress
    current_progress = 0
    try:
        # 이미지 생성
        image = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            callback=progress_callback,
            callback_steps=1
        ).images[0]

        # 이미지를 base64로 변환
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {"images": [img_str]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "Linaqruf/anything-v3.0", "device": device}

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with {model_id} model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)

