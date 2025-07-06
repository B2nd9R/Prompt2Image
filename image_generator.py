import asyncio
import aiohttp
import io
import logging
from typing import Optional, Dict, Any
from PIL import Image
import time
import json

logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, config):
        self.config = config
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        self.headers = {
            "Authorization": f"Bearer {config.huggingface_token}",
            "Content-Type": "application/json",
        }
        
        # نماذج متاحة
        self.models = {
            "stable-diffusion-xl": "stabilityai/stable-diffusion-xl-base-1.0",
            "stable-diffusion-2": "stabilityai/stable-diffusion-2-1",
            "midjourney": "prompthero/openjourney-v4",
            "anime": "hakurei/waifu-diffusion",
            "realistic": "runwayml/stable-diffusion-v1-5"
        }
        
        # إعدادات افتراضية
        self.default_settings = {
            "width": 512,
            "height": 512,
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
            "negative_prompt": "blurry, bad quality, distorted, ugly, low resolution"
        }
    
    async def generate_image(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 20,
        guidance_scale: float = 7.5,
        model: str = "stable-diffusion-xl"
    ) -> Optional[bytes]:
        """
        توليد صورة من وصف نصي
        """
        try:
            logger.info(f"بدء توليد صورة: {prompt[:50]}...")
            
            # تحسين الوصف
            enhanced_prompt = self._enhance_prompt(prompt)
            
            # إعداد البيانات
            payload = {
                "inputs": enhanced_prompt,
                "parameters": {
                    "negative_prompt": negative_prompt or self.default_settings["negative_prompt"],
                    "width": width,
                    "height": height,
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "seed": int(time.time())  # للحصول على نتائج متنوعة
                }
            }
            
            # تحديد النموذج المطلوب
            api_url = f"https://api-inference.huggingface.co/models/{self.models.get(model, self.models['stable-diffusion-xl'])}"
            
            # إرسال الطلب
            async with aiohttp.ClientSession() as session:
                image_data = await self._make_request(session, api_url, payload)
                
                if image_data:
                    # التحقق من صحة الصورة
                    if await self._validate_image(image_data):
                        logger.info("تم توليد الصورة بنجاح")
                        return image_data
                    else:
                        logger.error("الصورة المولدة غير صالحة")
                        return None
                else:
                    logger.error("فشل في توليد الصورة")
                    return None
                    
        except Exception as e:
            logger.error(f"خطأ في توليد الصورة: {str(e)}")
            return None
    
    async def _make_request(self, session: aiohttp.ClientSession, url: str, payload: Dict[str, Any]) -> Optional[bytes]:
        """
        إرسال طلب HTTP
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        if 'image' in content_type:
                            return await response.read()
                        else:
                            # قد يكون الرد JSON مع رسالة خطأ
                            text = await response.text()
                            logger.error(f"استجابة غير متوقعة: {text}")
                            
                            # إذا كان النموذج يحتاج وقت للتحميل
                            if "loading" in text.lower():
                                logger.info("النموذج يتم تحميله... انتظار...")
                                await asyncio.sleep(20)  # انتظار 20 ثانية
                                continue
                            
                            return None
                    
                    elif response.status == 503:
                        logger.warning(f"الخدمة غير متاحة، محاولة {attempt + 1}/{max_retries}")
                        await asyncio.sleep(retry_delay * (2 ** attempt))
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"خطأ HTTP {response.status}: {error_text}")
                        return None
            
            except Exception as e:
                logger.error(f"خطأ في الطلب، محاولة {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
        
        return None
    
    async def _validate_image(self, image_data: bytes) -> bool:
        """
        التحقق من صحة الصورة
        """
        try:
            # تحويل البيانات إلى صورة
            image = Image.open(io.BytesIO(image_data))
            
            # التحقق من أبعاد الصورة
            if image.size[0] < 50 or image.size[1] < 50:
                logger.error("الصورة صغيرة جداً")
                return False
            
            # التحقق من تنسيق الصورة
            if image.format not in ['PNG', 'JPEG', 'JPG']:
                logger.error(f"تنسيق الصورة غير مدعوم: {image.format}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"خطأ في التحقق من الصورة: {str(e)}")
            return False
    
    def _enhance_prompt(self, prompt: str) -> str:
        """
        تحسين الوصف النصي للحصول على نتائج أفضل
        """
        # إضافة كلمات مفتاحية لتحسين الجودة
        quality_keywords = [
            "high quality", "detailed", "sharp", "professional",
            "4k", "hd", "masterpiece", "best quality"
        ]
        
        # إضافة كلمات تقنية حسب نوع الصورة
        if any(word in prompt.lower() for word in ['person', 'face', 'portrait', 'human']):
            quality_keywords.extend(["realistic", "photorealistic", "skin texture"])
        
        if any(word in prompt.lower() for word in ['landscape', 'nature', 'outdoor']):
            quality_keywords.extend(["natural lighting", "scenic", "atmospheric"])
        
        if any(word in prompt.lower() for word in ['art', 'painting', 'drawing']):
            quality_keywords.extend(["artistic", "creative", "expressive"])
        
        # دمج الكلمات المفتاحية
        enhanced = f"{prompt}, {', '.join(quality_keywords[:3])}"
        
        return enhanced
    
    async def generate_variations(self, prompt: str, count: int = 4) -> list:
        """
        توليد عدة صور متنوعة للوصف نفسه
        """
        variations = []
        
        for i in range(count):
            # تنويع الوصف قليلاً
            varied_prompt = self._add_variation(prompt, i)
            
            image_data = await self.generate_image(varied_prompt)
            if image_data:
                variations.append({
                    "prompt": varied_prompt,
                    "image_data": image_data
                })
        
        return variations
    
    def _add_variation(self, prompt: str, index: int) -> str:
        """
        إضافة تنويع للوصف
        """
        variations = [
            ", artistic style",
            ", cinematic lighting",
            ", vibrant colors",
            ", soft lighting",
            ", dramatic shadows",
            ", minimalist style"
        ]
        
        if index < len(variations):
            return prompt + variations[index]
        
        return prompt
    
    def get_available_models(self) -> Dict[str, str]:
        """
        الحصول على قائمة النماذج المتاحة
        """
        return self.models
    
    async def test_connection(self) -> bool:
        """
        اختبار الاتصال بـ API
        """
        try:
            test_prompt = "a simple test image"
            image_data = await self.generate_image(test_prompt)
            return image_data is not None
        except Exception as e:
            logger.error(f"فشل اختبار الاتصال: {str(e)}")
            return False