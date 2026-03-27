"""
Remove.bg 开源替代 - 后端服务
FastAPI + rembg (U²-Net 模型)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from rembg import remove, new_session
from PIL import Image
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Remove.bg Free",
    description="开源免费背景移除工具",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化轻量级模型会话 (u2netp - 1.1MB, 速度快)
session = None


@app.on_event("startup")
async def startup_event():
    global session
    logger.info("正在加载 u2netp 模型...")
    session = new_session(model_name="u2netp")
    logger.info("模型加载完成")


@app.get("/")
async def root():
    return {
        "message": "Remove.bg Free API",
        "version": "0.1.0",
        "status": "running",
        "model": "u2netp (lightweight)"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "model_loaded": session is not None}


@app.post("/api/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    """
    P0: 单张图片背景移除
    支持格式：PNG, JPG, JPEG, WEBP
    """
    # 验证文件类型
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{file.content_type}。支持：PNG, JPG, WEBP"
        )
    
    try:
        # 读取图片
        image_data = await file.read()
        input_image = Image.open(io.BytesIO(image_data))
        
        # 移除背景
        output_image = remove(input_image, session=session)
        
        # 输出为 PNG
        output_buffer = io.BytesIO()
        output_image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        
        return Response(
            content=output_buffer.getvalue(),
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{file.filename.rsplit(".", 1)[0]}_no_bg.png"'
            }
        )
    
    except Exception as e:
        logger.error(f"处理失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败：{str(e)}")


@app.post("/api/batch-remove-bg")
async def batch_remove_background(files: list[UploadFile] = File(...)):
    """
    P1: 批量处理（最多 10 张）
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="最多支持 10 张图片同时处理"
        )
    
    results = []
    
    for file in files:
        try:
            image_data = await file.read()
            input_image = Image.open(io.BytesIO(image_data))
            output_image = remove(input_image, session=session)
            
            output_buffer = io.BytesIO()
            output_image.save(output_buffer, format="PNG")
            output_buffer.seek(0)
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "data": output_buffer.getvalue().hex()  # 临时方案，实际应该用 zip
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    return {"results": results, "total": len(files), "success": sum(1 for r in results if r["status"] == "success")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
