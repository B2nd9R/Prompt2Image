from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from datetime import datetime
import uuid
from typing import Optional
import logging

from image_generator import ImageGenerator
from utils.save_image import ImageSaver
from utils.config import Config

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء التطبيق
app = FastAPI(
    title="Prompt2Image API",
    description="توليد صور من وصف نصي باستخدام الذكاء الاصطناعي",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# إعداد الملفات الثابتة
if not os.path.exists("output"):
    os.makedirs("output")
    
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

# إعداد المولدات
config = Config()
image_generator = ImageGenerator(config)
image_saver = ImageSaver()

# نماذج البيانات
class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: Optional[int] = 512
    height: Optional[int] = 512
    num_inference_steps: Optional[int] = 20
    guidance_scale: Optional[float] = 7.5

class ImageResponse(BaseModel):
    success: bool
    message: str
    image_id: Optional[str] = None
    image_url: Optional[str] = None
    filename: Optional[str] = None
    prompt: Optional[str] = None

# المسارات
@app.get("/")
async def root():
    """الصفحة الرئيسية"""
    return {
        "message": "مرحباً بك في Prompt2Image API",
        "description": "توليد صور من وصف نصي باستخدام الذكاء الاصطناعي",
        "endpoints": {
            "generate": "/generate - إنشاء صورة جديدة",
            "gallery": "/gallery - عرض جميع الصور",
            "docs": "/docs - وثائق API"
        }
    }

@app.post("/generate", response_model=ImageResponse)
async def generate_image(request: ImageRequest, background_tasks: BackgroundTasks):
    """توليد صورة من وصف نصي"""
    try:
        logger.info(f"بدء توليد صورة للوصف: {request.prompt}")
        
        # توليد معرف فريد للصورة
        image_id = str(uuid.uuid4())
        
        # توليد الصورة
        image_data = await image_generator.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale
        )
        
        if not image_data:
            raise HTTPException(status_code=500, detail="فشل في توليد الصورة")
        
        # حفظ الصورة
        filename = await image_saver.save_image(
            image_data=image_data,
            prompt=request.prompt,
            image_id=image_id
        )
        
        # تسجيل العملية في الخلفية
        background_tasks.add_task(
            log_generation,
            image_id=image_id,
            prompt=request.prompt,
            filename=filename
        )
        
        logger.info(f"تم توليد الصورة بنجاح: {filename}")
        
        return ImageResponse(
            success=True,
            message="تم توليد الصورة بنجاح",
            image_id=image_id,
            image_url=f"/output/{filename}",
            filename=filename,
            prompt=request.prompt
        )
        
    except Exception as e:
        logger.error(f"خطأ في توليد الصورة: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في توليد الصورة: {str(e)}")

@app.get("/gallery")
async def get_gallery():
    """عرض جميع الصور المولدة"""
    try:
        images = []
        output_dir = "output"
        
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(output_dir, filename)
                    stat = os.stat(file_path)
                    
                    images.append({
                        "filename": filename,
                        "url": f"/output/{filename}",
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "size": stat.st_size
                    })
        
        # ترتيب حسب تاريخ الإنشاء (الأحدث أولاً)
        images.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "count": len(images),
            "images": images
        }
        
    except Exception as e:
        logger.error(f"خطأ في عرض المعرض: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في عرض المعرض: {str(e)}")

@app.get("/image/{filename}")
async def get_image(filename: str):
    """عرض صورة محددة"""
    file_path = os.path.join("output", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="الصورة غير موجودة")
    
    return FileResponse(file_path)

@app.delete("/image/{filename}")
async def delete_image(filename: str):
    """حذف صورة محددة"""
    try:
        file_path = os.path.join("output", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="الصورة غير موجودة")
        
        os.remove(file_path)
        logger.info(f"تم حذف الصورة: {filename}")
        
        return {
            "success": True,
            "message": f"تم حذف الصورة {filename} بنجاح"
        }
        
    except Exception as e:
        logger.error(f"خطأ في حذف الصورة: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في حذف الصورة: {str(e)}")

@app.get("/stats")
async def get_stats():
    """إحصائيات الاستخدام"""
    try:
        output_dir = "output"
        total_images = 0
        total_size = 0
        
        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    file_path = os.path.join(output_dir, filename)
                    total_images += 1
                    total_size += os.path.getsize(file_path)
        
        return {
            "total_images": total_images,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "average_size_mb": round((total_size / total_images) / (1024 * 1024), 2) if total_images > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على الإحصائيات: {str(e)}")
        raise HTTPException(status_code=500, detail=f"خطأ في الحصول على الإحصائيات: {str(e)}")

# المهام الخلفية
async def log_generation(image_id: str, prompt: str, filename: str):
    """تسجيل عملية التوليد"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "image_id": image_id,
            "prompt": prompt,
            "filename": filename
        }
        
        # يمكن إضافة المزيد من التسجيل هنا
        logger.info(f"تم تسجيل العملية: {log_entry}")
        
    except Exception as e:
        logger.error(f"خطأ في تسجيل العملية: {str(e)}")

# معالج الأخطاء
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"خطأ غير متوقع: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "حدث خطأ غير متوقع",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )