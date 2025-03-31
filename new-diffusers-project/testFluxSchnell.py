from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import FluxTransformer2DModel, FluxPipeline
from transformers import T5EncoderModel, CLIPTextModel
from optimum.quanto import freeze, qfloat8, quantize
import base64
from io import BytesIO
import os
from dotenv import load_dotenv
from huggingface_hub import login
# 로그 추적용
import logging
import traceback
# 로깅 설정
logging.basicConfig(level=logging.INFO)

# FastAPI 프레임워크를 사용해서 서버 생성
app = FastAPI()
load_dotenv()

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
local_model = "C:/models/flux/flux1-schnell-fp8.safetensors"

# CUDA(NVIDIA GPU) 사용 가능 여부 확인
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"using device: {device}")

# GPU사용시 정보 출력
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA 버전: {torch.version.cuda}")
    print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_memory/(1024**3):.2f} GB")
    print(f"사용가능 메모리: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB 사용, {torch.cuda.memory_reserved(0) / (1024**3):.2f} GB 예정")

dtype = torch.float16 if device == "cuda" else torch.float32

try:
    # 메모리 초기화
    if device == "cuda":
        torch.cuda.empty_cache()
        print("CUDA 캐시 비움")
    
    print("transformer 모델 불러오기")
    transformer = FluxTransformer2DModel.from_single_file(
        local_model,
        torch_dtype=dtype
    )
    print("transformer 모델 호출 성공")
    
    print("transformer GPU로 이동")
    transformer = transformer.to(device)
    print(f"transformer 디바이스: {next(transformer.parameters()).device}")
    
    print("transformer freeze 적용")
    freeze(transformer)
    print("transformer freeze 완료")
    
    print("text_encoder_2 로딩")
    text_encoder_2 = T5EncoderModel.from_pretrained(
        model_repo,
        subfolder="text_encoder_2",
        torch_dtype=dtype
    )
    print("text_encoder_2 로딩 완료")
    
    print("text_encoder_2 GPU로 이동")
    text_encoder_2 = text_encoder_2.to(device)
    print(f"text_encoder_2 디바이스: {next(text_encoder_2.parameters()).device}")
    
    print("text_encoder_2 freeze 적용")
    freeze(text_encoder_2)
    print("text_encoder_2 freeze 완료")
    
    print("파이프라인 생성")
    pipe = FluxPipeline.from_pretrained(
        model_repo,
        transformer=None,
        text_encoder_2=None,
        torch_dtype=dtype
    )
    print("파이프라인 로딩 완료")
    
    # 모든 서브 모델을 명시적으로 GPU로 이동
    print("파이프라인 컴포넌트를 GPU로 이동 중...")
    
    # 파이프라인 구성요소들을 명시적으로 GPU로 이동
    for name, module in pipe.named_components.items():
        if module is not None:
            print(f"컴포넌트 {name}를 {device}로 이동")
            pipe.named_components[name] = module.to(device)
    
    # 파이프라인 자체를 GPU로 이동
    pipe = pipe.to(device)
    
    print("모델 할당")
    pipe.transformer = transformer
    pipe.text_encoder_2 = text_encoder_2
    
    # 파이프라인이 올바른 디바이스에 있는지 확인
    for name, module in pipe.named_components.items():
        if module is not None and hasattr(module, 'parameters') and any(True for _ in module.parameters()):
            try:
                device_info = next(module.parameters()).device
                print(f"컴포넌트 {name}의 디바이스: {device_info}")
                if str(device_info) != device and str(device_info) != f"cuda:{torch.cuda.current_device()}" and device == "cuda":
                    print(f"경고: 컴포넌트 {name}가 다른 디바이스에 있습니다. {device}로 이동합니다.")
                    pipe.named_components[name] = module.to(device)
            except StopIteration:
                print(f"컴포넌트 {name}에 매개변수가 없습니다.")
    
    print("메모리 최적화")
    pipe.enable_attention_slicing(1)
    print("메모리 최적화 완료")
    
except Exception as e:
    print(f"모델 호출 에러: {e}")
    traceback.print_exc()
    raise RuntimeError(f"모델 초기화 실패; {e}")

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_inference_steps: int = 15
    guidance_scale: float = 2.5

# 이미지 생성 엔드포인트
@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    try:
        print(f"Generating image with prompt: {request.prompt}")
        print(f"현재 메모리 상태: {torch.cuda.memory_allocated(0) / (1024**3):.2f} GB 사용")
        
        # 메모리 확보
        if device == "cuda":
            torch.cuda.empty_cache()
        
        # 입력 텐서를 올바른 디바이스로 이동 확인
        for name, module in pipe.named_components.items():
            if module is not None and hasattr(module, 'parameters') and any(True for _ in module.parameters()):
                try:
                    current_device = next(module.parameters()).device
                    if str(current_device) != device and str(current_device) != f"cuda:{torch.cuda.current_device()}" and device == "cuda":
                        print(f"경고: 컴포넌트 {name}가 {current_device}에 있습니다. {device}로 이동합니다.")
                        pipe.named_components[name] = module.to(device)
                except StopIteration:
                    pass
                
        # 이미지 생성 
        image = pipe(
            request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=15,
            guidance_scale=2.5,
            output_type="pil",
            generator=torch.Generator(device).manual_seed(0)
        ).images[0]
        
        # base64 인코딩된 문자열로 변환
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        print("이미지 생성 완료")
        return {"images": [img_str]}
    except Exception as e:
        error_msg = f"이미지 생성 실패: {str(e)}"
        traceback_str = traceback.format_exc()
        print(error_msg)
        print(traceback_str)
        logging.error(f"{error_msg}\n{traceback_str}")
        return {"error": error_msg, "traceback": traceback_str}

# 서버 상태 확인
@app.get("/health")
async def health_check():
    component_devices = {}
    
    try:
        # 각 컴포넌트의 디바이스 정보 수집
        for name, module in pipe.named_components.items():
            if module is not None and hasattr(module, 'parameters') and any(True for _ in module.parameters()):
                try:
                    component_devices[name] = str(next(module.parameters()).device)
                except StopIteration:
                    component_devices[name] = "no parameters"
    except Exception as e:
        component_devices["error"] = str(e)
        
    return {
        "status": "healthy",
        "model": model_repo,
        "device": device,
        "gpu_info": torch.cuda.get_device_name(0) if device == "cuda" else "N/A",
        "component_devices": component_devices
    }

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with Flux model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)