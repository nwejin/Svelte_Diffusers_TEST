from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import FluxTransformer2DModel, FluxPipeline, GGUFQuantizationConfig
from transformers import T5EncoderModel, CLIPTextModel
from optimum.quanto import freeze, qfloat8, quantize

import base64
from io import BytesIO
import os
from dotenv import load_dotenv
from huggingface_hub import login
import logging


# 로깅 설정
logging.basicConfig(level=logging.ERROR)

# FastAPI 프레임워크를 사용해서 서버 생성
app = FastAPI()
load_dotenv()

# hf_token = os.getenv("HUGGINGFACE_TOKEN")

# if hf_token:
#     login(token=hf_token)
#     print(" 로그인 성공!")
# else:
#     print("로그인 에러")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 사용 모델
model_repo = "black-forest-labs/FLUX.1-schnell"
# black-forest-labs/FLUX.1-schnell
# black-forest-labs/FLUX.1-dev
# Comfy-Org/flux1-schnell

guff_path = "https://huggingface.co/city96/FLUX.1-schnell-gguf/blob/main/flux1-schnell-Q4_0.gguf"



local_model = "C:/models/flux/flux1-schnell-fp8.safetensors"

# C:/models/flux/flux1-schnell-fp8.safetensors
# C:/models/flux/flux1-schnell-Q4_0.gguf


# CUDA(NVIDIA GPU) 사용 가능 여부 확인
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"using device: {device}")

# GPU사용시 정보 출력
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")


# 단일 파일에서 transformer 모델 로드
transformer = FluxTransformer2DModel.from_single_file(
    guff_path,
    quantization_config =GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
    torch_dtype=torch.bfloat16
    )


# 파이프라인 생성
pipe = FluxPipeline.from_pretrained(
    model_repo, 
    transformer=transformer,
    torch_dtype=torch.bfloat16,
    )

pipe.enable_model_cpu_offload()

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 768
    height: int = 1024
    num_inference_steps: int = 4  
    guidance_scale: float = 0.0

# 이미지 생성 엔드포인트
@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    try:
        print(f"Generating image with prompt: {request.prompt}")
        # 이미지 생성
        image = pipe(
            request.prompt,
            # negative_prompt=request.negative_prompt,
            width=768,
            height=1024,
            num_inference_steps=4, 
            guidance_scale=0.0,
            output_type="pil",
            generator=torch.Generator("cuda" if device == "cuda" else "cpu").manual_seed(0)
        ).images[0]

        # base64 인코딩된 문자열로 변환
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {"images": [img_str]}

    except Exception as e:
        logging.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 서버 상태 확인
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "model": "Comfy-Org/flux1-schnell", 
        "device": device,
        "gpu_info": torch.cuda.get_device_name(0) if device == "cuda" else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with Flux model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)