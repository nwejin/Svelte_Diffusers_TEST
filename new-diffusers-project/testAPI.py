from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import StableDiffusionPipeline
import base64
from io import BytesIO

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
    steps: int = 20  # 클라이언트 요청에 맞게 필드명 수정
    cfg_scale: float = 7.0  # 클라이언트 요청에 맞게 필드명 수정
    sampler_name: str = "Euler a"  # 클라이언트에서 보내는 이 필드 추가

@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    try:
        # 이미지 생성 - 콜백 관련 파라미터 제거
        image = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.steps,  # 필드명 수정
            guidance_scale=request.cfg_scale,  # 필드명 수정
            # callback과 callback_steps 파라미터 제거
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
    return {"status": "healthy", "model": model_id, "device": device}

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with {model_id} model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)