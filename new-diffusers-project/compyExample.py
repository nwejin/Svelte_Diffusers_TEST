from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import websocket
import uuid
import json
import urllib.request
import urllib.parse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
     allow_origins=["http://localhost:5173"], 
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

COMFY_SERVER = "http://127.0.0.1:8188"
COMFY_WS = "ws://127.0.0.1:8188/ws"


class PromptRequest(BaseModel):
    prompt: Dict[str, Any]
    client_id: Optional[str] = None

# CompyUI에 이미지 생성 요청
def queue_prompt(prompt, client_id=None):
    if not client_id:
        client_id = str(uuid.uuid4())
    
    p = {
        "prompt": prompt,
        "client_id": client_id
    }
    
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request(f"{COMFY_SERVER}/prompt", data=data, method="POST")

    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except Exception as e:
        # 에러 발생
        raise HTTPException(status_code=500, detail=f"ComfyUI 서버 오류: {str(e)}")

# 이미지 가져오기
def fetch_image(filename, subfolder, folder_type):
    try:
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"{COMFY_SERVER}/view?{url_values}") as response:
            return response.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 가져오기 오류: {str(e)}")
        
# 히스토리 데이터 가져오기
def fetch_history(prompt_id):
    try:
        with urllib.request.urlopen(f"{COMFY_SERVER}/history/{prompt_id}") as response:
            return json.loads(response.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 데이터 가져오기 오류: {str(e)}")

# 엔드포인트
# 이미지 생성
@app.post('/api/generate-image')
async def generate_image(request: PromptRequest):
    try:
        result = queue_prompt(request.prompt, request.client_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 생성 오류: {str(e)}")

# 이미지 미리보기
@app.get('/api/image')
async def get_image_preview(filename: str, subfolder: str = "", folder_type: str = "output"):
    try:
        image_data = fetch_image(filename, subfolder, folder_type)
        return Response(content=image_data, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이미지 호출 오류: {str(e)}")
    

#히스토리 데이터 가져오기
@app.get('/api/history/{prompt_id}')
async def get_prompt_history(prompt_id: str):
    try:
        history_data = fetch_history(prompt_id)
        return history_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 호출 오류: {str(e)}")
    

if __name__ == "__main__":
    import uvicorn
    print("파이썬 FastAPI 서버 실행")
    uvicorn.run(app, host="0.0.0.0", port=8000)
