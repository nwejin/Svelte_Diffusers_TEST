from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import StableDiffusionPipeline
import base64
from io import BytesIO

# FastAPI 프레임워크를 사용해서 서버 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_id = "runwayml/stable-diffusion-v1-5" 

# CUDA(NVIDIA GPU) 사용 가능 여부 확인
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"using device: {device}")

# GPU 정보 출력
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")

# 데이터 타입 설정 (CUDA에서는 half precision 사용 가능)
dtype = torch.float16 if device == "cuda" else torch.float32

# Stable Diffusion의 전체 과정을 하나의 파이프라인으로 처리
pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=dtype,
)

pipe = pipe.to(device)
# 모델 성능 최적화
pipe.enable_attention_slicing()
pipe.enable_vae_tiling()

# 메모리 최적화 (GPU 메모리가 제한적인 경우)
if device == "cuda" and torch.cuda.get_device_properties(0).total_memory < 8 * 1024 * 1024 * 1024:  # 8GB 미만
    pipe.enable_sequential_cpu_offload()

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20  
    cfg_scale: float = 7.0 
    sampler_name: str = "Euler a"


# 이미지 생성 엔드포인트
@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    try:
        # 이미지 생성
        image = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.steps, 
            guidance_scale=request.cfg_scale,
            # CUDA 디바이스에서는 CUDA 생성기 사용
            generator = torch.Generator("cuda" if device == "cuda" else "cpu").manual_seed(0)
        ).images[0]

        # base64 인코딩된 문자열로 변환
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {"images": [img_str]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 서버 상태 확인
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model": model_id, 
        "device": device,
        "gpu_info": torch.cuda.get_device_name(0) if device == "cuda" else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with {model_id} model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)