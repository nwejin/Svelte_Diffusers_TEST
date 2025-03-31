from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import requests
import json
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import uuid
import traceback


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMFY_URL = "http://localhost:8188"

with open("./workflowJSON/20250331WF.json", "r") as f:
    default_workflow = json.load(f)

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""

@app.post("/generate")
async def generate_image(req: TextToImageRequest):
    try:
        workflow = default_workflow.copy()
        
        # 프롬프트 설정
        if "6" in workflow:  # 노드 ID 6 (CLIPTextEncode)
            workflow["6"]["inputs"]["text"] = req.prompt
            print(f"프롬프트 설정: {req.prompt}")
        
        if "7" in workflow:  # 노드 ID 7 (CLIPTextEncode - negative)
            workflow["7"]["inputs"]["text"] = req.negative_prompt
            print(f"네거티브 프롬프트 설정: {req.negative_prompt}")
        
        # 랜덤 시드 생성
        import random
        random_seed = random.randint(1, 2**32 - 1)
        if "3" in workflow:  # 노드 ID 3 (KSampler)
            workflow["3"]["inputs"]["seed"] = random_seed
            print(f"랜덤 시드 설정: {random_seed}")
        
        client_id = str(uuid.uuid4())
        print(f"클라이언트 ID: {client_id}")
        
        # ComfyUI 요청 보내기
        print("ComfyUI 서버에 요청 전송 중...")
        res = requests.post(
            f"{COMFY_URL}/prompt",
            json={"prompt": workflow, "client_id": client_id}
        )

        if res.status_code != 200:
            print(f"ComfyUI 서버 응답 오류: {res.status_code}, {res.text}")
            raise HTTPException(status_code=500, detail=f"ComfyUI 서버 오류: {res.text}")

        prompt_id = res.json().get("prompt_id")
        if not prompt_id:
            print("prompt_id를 받지 못했습니다.")
            raise HTTPException(status_code=500, detail="ComfyUI 서버에서 prompt_id를 받지 못했습니다.")
            
        print(f"Prompt ID: {prompt_id}")

        # 결과 대기
        output_images = []
        seed = None

        max_attempts = 60  # 시간 증가 (60초)
        attempts = 0

        print("이미지 생성 결과 대기 중...")
        while attempts < max_attempts:
            try:
                history_resp = requests.get(f"{COMFY_URL}/history/{client_id}")
                if history_resp.status_code == 200:
                    history = history_resp.json()
                    
                    if prompt_id in history:
                        print(f"히스토리에서 prompt_id {prompt_id} 찾음")
                        
                        # 오류 확인
                        if "error" in history[prompt_id]:
                            error_msg = history[prompt_id]["error"]
                            print(f"ComfyUI 처리 오류: {error_msg}")
                            raise HTTPException(status_code=500, detail=f"ComfyUI 처리 오류: {error_msg}")
                        
                        # 출력 확인
                        if "outputs" in history[prompt_id]:
                            outputs = history[prompt_id]["outputs"]
                            print(f"출력 노드 ID: {list(outputs.keys())}")

                            for node_id, node_output in outputs.items():
                                if "images" in node_output:
                                    for img in node_output["images"]:
                                        output_images.append(img["filename"])
                                        print(f"이미지 파일 발견: {img['filename']}")
                            
                            # 시드 값 확인
                            if "3" in workflow:
                                seed = workflow["3"]["inputs"]["seed"]
                                print(f"사용된 시드 값: {seed}")
                            
                            if output_images:
                                print("이미지 생성 완료!")
                                break
            except Exception as e:
                print(f"히스토리 확인 중 오류: {str(e)}")
                print(traceback.format_exc())
                # 여기서는 예외를 발생시키지 않고 계속 시도합니다
            
            attempts += 1
            print(f"대기 중... 시도 {attempts}/{max_attempts}")
            time.sleep(1)

        if not output_images:
            print("이미지를 찾을 수 없음 (시간초과)")
            raise HTTPException(status_code=500, detail="이미지 생성 실패 또는 시간초과")
        
        image_url = f"{COMFY_URL}/view?filename={output_images[0]}"
        print(f"반환 이미지 URL: {image_url}")
        
        # 이미지 URL 유효성 확인
        try:
            img_check = requests.head(image_url)
            if img_check.status_code != 200:
                print(f"이미지 URL 확인 실패: {img_check.status_code}")
                raise HTTPException(status_code=500, detail="생성된 이미지를 확인할 수 없습니다")
        except Exception as e:
            print(f"이미지 URL 확인 중 오류: {str(e)}")
            # 계속 진행 (URL이 유효하지만 HEAD 요청이 지원되지 않을 수 있음)
        
        return {
            "image_url": image_url,
            "seed": seed
        }
        
    except HTTPException:
        # 이미 처리된 HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"예상치 못한 오류: {str(e)}")
        print(error_trace)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.get("/health")
async def health_check():
    """서버 상태 확인 엔드포인트"""
    return {"status": "ok", "comfy_url": COMFY_URL}

if __name__ == "__main__":
    import uvicorn
    print("FastAPI 서버 시작 중 - http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)