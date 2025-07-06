# استخدام Python 3.11 slim كأساس
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# تثبيت الحزم النظامية المطلوبة
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات
COPY requirements.txt .

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# إنشاء المجلدات المطلوبة
RUN mkdir -p output static logs

# تعيين صلاحيات المجلدات
RUN chmod -R 755 output static logs

# إنشاء مستخدم غير جذر
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# تعيين المتغيرات البيئية
ENV HOST=0.0.0.0 \
    PORT=8000 \
    OUTPUT_DIR=/app/output \
    LOG_LEVEL=INFO

# كشف المنفذ
EXPOSE 8000

# إنشاء صحة النظام
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# تشغيل التطبيق
CMD ["python", "main.py"]

# أو يمكن استخدام uvicorn مباشرة
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]