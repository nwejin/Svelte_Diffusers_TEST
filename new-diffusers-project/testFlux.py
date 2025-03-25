from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel, CLIPTextModel
import base64
from io import BytesIO

# 필요한 경우 optimum-quanto 설치
# pip install optimum-quanto
from optimum.quanto import freeze, qfloat8, quantize

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

# CUDA(NVIDIA GPU) 사용 가능 여부 확인
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"using device: {device}")

# GPU 정보 출력
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")

# 데이터 타입 설정 (CUDA에서는 half precision 사용 가능)
dtype = torch.float16 if device == "cuda" else torch.float32

# 기본 Flux 모델 저장소
bfl_repo = "black-forest-labs/FLUX.1-dev"

# 단일 파일에서 transformer 모델 로드
transformer = FluxTransformer2DModel.from_single_file(
    "https://huggingface.co/Comfy-Org/flux1-schnell/raw/main/flux1-schnell-fp8.safetensors", 
    torch_dtype=dtype
)

# GPU 메모리가 충분하다면 FP8 양자화 사용
if device == "cuda" and torch.cuda.get_device_properties(0).total_memory > 8 * 1024 * 1024 * 1024:  # 8GB 이상
    try:
        print("Applying FP8 quantization...")
        quantize(transformer, weights=qfloat8)
        freeze(transformer)
    except Exception as e:
        print(f"FP8 quantization failed: {e}. Continuing without quantization.")

# 기본 모델에서 text_encoder_2 로드
text_encoder_2 = T5EncoderModel.from_pretrained(bfl_repo, subfolder="text_encoder_2", torch_dtype=dtype)

# GPU 메모리가 충분하다면 text_encoder_2에도 FP8 양자화 적용
if device == "cuda" and torch.cuda.get_device_properties(0).total_memory > 8 * 1024 * 1024 * 1024:
    try:
        quantize(text_encoder_2, weights=qfloat8)
        freeze(text_encoder_2)
    except Exception as e:
        print(f"Text encoder FP8 quantization failed: {e}")

# 파이프라인 생성
pipe = FluxPipeline.from_pretrained(bfl_repo, transformer=None, text_encoder_2=None, torch_dtype=dtype)
pipe.transformer = transformer
pipe.text_encoder_2 = text_encoder_2

# 디바이스 설정
if device == "cuda":
    # 메모리가 적은 GPU에서는 모델 CPU 오프로딩 사용
    if torch.cuda.get_device_properties(0).total_memory < 8 * 1024 * 1024 * 1024:  # 8GB 미만
        pipe.enable_model_cpu_offload()
    else:
        pipe = pipe.to(device)
else:
    pipe = pipe.to(device)

# 메모리 최적화 (GPU 메모리가 제한적인 경우)
pipe.enable_attention_slicing()  # 주의: Flux에서 지원하지 않는 경우 이 줄을 제거하세요

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_inference_steps: int = 20  
    guidance_scale: float = 7.0 

# 이미지 생성 엔드포인트
@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    try:
        # 이미지 생성
        image = pipe(
            request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps, 
            guidance_scale=request.guidance_scale,
            output_type="pil",
            generator=torch.Generator(device == "cuda").manual_seed(0) if device == "cuda" else torch.Generator("cpu").manual_seed(0)
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
        "model": "Comfy-Org/flux1-schnell", 
        "device": device,
        "gpu_info": torch.cuda.get_device_name(0) if device == "cuda" else "N/A"
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with Flux model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)