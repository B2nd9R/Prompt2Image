# 🎨 Prompt2Image - مولد الصور بالذكاء الاصطناعي

## نظرة عامة

**Prompt2Image** هو مشروع Python متكامل لتوليد الصور من النصوص باستخدام الذكاء الاصطناعي. يستخدم المشروع FastAPI لإنشاء API قوي وسهل الاستخدام مع دعم HuggingFace للحصول على نماذج ذكاء اصطناعي مجانية.

## ✨ المميزات

- 🚀 **سريع وفعال**: مبني على FastAPI
- 🎯 **متعدد النماذج**: دعم لعدة نماذج ذكاء اصطناعي
- 💾 **إدارة ذكية للملفات**: حفظ تلقائي مع metadata
- 🔒 **آمن**: حدود للاستخدام وتنظيف تلقائي
- 🌐 **API شامل**: واجهة RESTful كاملة
- 🎨 **علامة مائية**: إضافة تلقائية لحماية الصور
- 📊 **إحصائيات**: مراقبة الاستخدام والأداء

## 🛠️ التثبيت

### 1. استنساخ المشروع

```bash
git clone https://github.com/yourusername/prompt2image.git
cd prompt2image
```

### 2. إنشاء البيئة الافتراضية

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows
```

### 3. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 4. إعداد متغيرات البيئة

إنشاء ملف `.env` في المجلد الرئيسي:

```env
# HuggingFace Token (مطلوب)
HUGGINGFACE_TOKEN=your_huggingface_token_here

# إعدادات اختيارية
DEFAULT_WIDTH=512
DEFAULT_HEIGHT=512
OUTPUT_DIR=output
MAX_STORAGE_MB=1000
RATE_LIMIT_PER_MINUTE=10
TIMEOUT_SECONDS=60
```

## 🚀 التشغيل

### تشغيل الخادم

```bash
python main.py
```

أو باستخدام uvicorn مباشرة:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### الوصول للتطبيق

- **API الرئيسي**: http://localhost:8000
- **الوثائق التفاعلية**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 استخدام API

### 1. توليد صورة جديدة

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "width": 512,
    "height": 512,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
  }'
```

### 2. عرض معرض الصور

```bash
curl -X GET "http://localhost:8000/gallery"
```

### 3. الحصول على إحصائيات

```bash
curl -X GET "http://localhost:8000/stats"
```

### 4. حذف صورة

```bash
curl -X DELETE "http://localhost:8000/image/filename.png"
```

## 🏗️ هيكل المشروع

```
prompt2image/
├── main.py                 # FastAPI الرئيسي
├── image_generator.py      # مولد الصور
├── utils/
│   ├── save_image.py      # حفظ الصور
│   └── config.py          # إعدادات التطبيق
├── output/                # الصور المولدة
├── static/                # الملفات الثابتة
├── requirements.txt       # المتطلبات
├── README.md             # هذا الملف
└── .env                  # متغيرات البيئة
```

## 🎯 أمثلة للاستخدام

### Python Client

```python
import requests
import json

# توليد صورة
response = requests.post(
    "http://localhost:8000/generate",
    json={
        "prompt": "A futuristic cyberpunk city at night",
        "negative_prompt": "blurry, low quality",
        "width": 768,
        "height": 512
    }
)

result = response.json()
print(f"تم إنشاء الصورة: {result['image_url']}")
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function generateImage() {
    try {
        const response = await axios.post('http://localhost:8000/generate', {
            prompt: 'A magical forest with glowing trees',
            width: 512,
            height: 512
        });
        
        console.log('Image generated:', response.data.image_url);
    } catch (error) {
        console.error('Error:', error.response.data);
    }
}

generateImage();
```

## ⚙️ إعدادات متقدمة

### إعداد config.json

```json
{
  "default_width": 512,
  "default_height": 512,
  "max_width": 1024,
  "max_height": 1024,
  "default_steps": 25,
  "max_steps": 50,
  "default_guidance": 7.5,
  "output_dir": "output",
  "max_storage_mb": 2000,
  "auto_cleanup_days": 30,
  "rate_limit_per_minute": 10,
  "timeout_seconds": 60,
  "enable_watermark": true,
  "enable_metadata": true
}
```

### النماذج المتاحة

- **stable-diffusion-xl**: الأفضل للجودة العالية
- **stable-diffusion-2**: متوازن بين الجودة والسرعة
- **midjourney**: لأسلوب فني مميز
- **anime**: للرسوم المتحركة
- **realistic**: للصور الواقعية

## 🔧 التطوير

### تشغيل الاختبارات

```bash
pytest tests/
```

### تنسيق الكود

```bash
black .
flake8 .
```

### إضافة ميزات جديدة

1. قم بإنشاء branch جديد
2. أضف الميزة الجديدة
3. اكتب اختبارات
4. قم بإرسال Pull Request

## 📊 مراقبة الأداء

### معلومات الاستخدام

```bash
curl -X GET "http://localhost:8000/stats"
```

### تنظيف الملفات القديمة

```python
from utils.save_image import ImageSaver

saver = ImageSaver()
deleted_count = saver.cleanup_old_images(days_old=30)
print(f"تم حذف {deleted_count} صورة قديمة")
```

## 🚨 استكشاف الأخطاء

### مشاكل شائعة

1. **خطأ في HuggingFace Token**
   - تأكد من صحة التوكن
   - تحقق من صلاحية التوكن

2. **بطء في التوليد**
   - قلل عدد الخطوات
   - استخدم أبعاد أصغر

3. **نفاد المساحة**
   - قم بتشغيل تنظيف تلقائي
   - زيادة حد التخزين

### رسائل الخطأ

```
Error: Model is loading
الحل: انتظر 1-2 دقيقة حتى يتم تحميل النموذج
```

## 🔐 الأمان

- حدود معدل الطلبات
- تنظيف تلقائي للملفات
- تحقق من صحة المدخلات
- حماية ضد الهجمات

## 📝 التراخيص

هذا المشروع مرخص تحت MIT License. راجع ملف LICENSE للتفاصيل.

## 🤝 المساهمة

نرحب بالمساهمات! يرجى قراءة CONTRIBUTING.md للتفاصيل.

## 📞 الدعم

- إنشاء issue على GitHub
- إرسال email للدعم
- زيارة الوثائق

## 🔮 الخطط المستقبلية

- [ ] دعم المزيد من النماذج
- [ ] واجهة ويب تفاعلية
- [ ] دعم الترجمة التلقائية
- [ ] تحسين الأداء
- [ ] دعم الصور عالية الدقة
- [ ] إضافة فلاتر وتأثيرات

## 🏆 الائتمان

- **HuggingFace**: للنماذج والAPI
- **FastAPI**: لإطار العمل
- **Pillow**: لمعالجة الصور
- **OpenAI**: للإلهام في التصميم

---

**استمتع بتوليد الصور الرائعة! 🎨✨**