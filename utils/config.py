import os
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Config:
    """
    إعدادات التطبيق
    """
    # إعدادات HuggingFace
    huggingface_token: Optional[str] = None
    
    # إعدادات الصور
    default_width: int = 512
    default_height: int = 512
    max_width: int = 1024
    max_height: int = 1024
    
    # إعدادات الجودة
    default_steps: int = 20
    max_steps: int = 50
    default_guidance: float = 7.5
    
    # إعدادات التخزين
    output_dir: str = "output"
    max_storage_mb: int = 1000
    auto_cleanup_days: int = 30
    
    # إعدادات API
    rate_limit_per_minute: int = 10
    timeout_seconds: int = 60
    
    # إعدادات الأمان
    allowed_file_types: list = None
    max_prompt_length: int = 500
    
    # إعدادات الواجهة
    enable_watermark: bool = True
    enable_metadata: bool = True
    
    def __post_init__(self):
        """تحميل الإعدادات من متغيرات البيئة أو ملف الإعدادات"""
        self.load_from_env()
        self.load_from_file()
        
        if self.allowed_file_types is None:
            self.allowed_file_types = ['.png', '.jpg', '.jpeg']
    
    def load_from_env(self):
        """تحميل الإعدادات من متغيرات البيئة"""
        self.huggingface_token = os.getenv('HUGGINGFACE_TOKEN', self.huggingface_token)
        
        # إعدادات الصور
        if os.getenv('DEFAULT_WIDTH'):
            self.default_width = int(os.getenv('DEFAULT_WIDTH'))
        if os.getenv('DEFAULT_HEIGHT'):
            self.default_height = int(os.getenv('DEFAULT_HEIGHT'))
        
        # إعدادات التخزين
        if os.getenv('OUTPUT_DIR'):
            self.output_dir = os.getenv('OUTPUT_DIR')
        if os.getenv('MAX_STORAGE_MB'):
            self.max_storage_mb = int(os.getenv('MAX_STORAGE_MB'))
        
        # إعدادات API
        if os.getenv('RATE_LIMIT_PER_MINUTE'):
            self.rate_limit_per_minute = int(os.getenv('RATE_LIMIT_PER_MINUTE'))
        if os.getenv('TIMEOUT_SECONDS'):
            self.timeout_seconds = int(os.getenv('TIMEOUT_SECONDS'))
    
    def load_from_file(self, config_file: str = "config.json"):
        """تحميل الإعدادات من ملف JSON"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # تحديث الإعدادات
                for key, value in config_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                logger.info(f"تم تحميل الإعدادات من: {config_file}")
        except Exception as e:
            logger.error(f"خطأ في تحميل ملف الإعدادات: {str(e)}")
    
    def save_to_file(self, config_file: str = "config.json"):
        """حفظ الإعدادات في ملف JSON"""
        try:
            config_data = {
                "default_width": self.default_width,
                "default_height": self.default_height,
                "max_width": self.max_width,
                "max_height": self.max_height,
                "default_steps": self.default_steps,
                "max_steps": self.max_steps,
                "default_guidance": self.default_guidance,
                "output_dir": self.output_dir,
                "max_storage_mb": self.max_storage_mb,
                "auto_cleanup_days": self.auto_cleanup_days,
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "timeout_seconds": self.timeout_seconds,
                "allowed_file_types": self.allowed_file_types,
                "max_prompt_length": self.max_prompt_length,
                "enable_watermark": self.enable_watermark,
                "enable_metadata": self.enable_metadata
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"تم حفظ الإعدادات في: {config_file}")
            
        except Exception as e:
            logger.error(f"خطأ في حفظ ملف الإعدادات: {str(e)}")
    
    def validate(self) -> Dict[str, Any]:
        """التحقق من صحة الإعدادات"""
        errors = []
        warnings = []
        
        # التحقق من توكن HuggingFace
        if not self.huggingface_token:
            errors.append("HuggingFace token is required")
        
        # التحقق من أبعاد الصور
        if self.default_width <= 0 or self.default_height <= 0:
            errors.append("Image dimensions must be positive")
        
        if self.default_width > self.max_width or self.default_height > self.max_height:
            warnings.append("Default dimensions exceed maximum allowed")
        
        # التحقق من إعدادات الجودة
        if self.default_steps <= 0 or self.default_steps > self.max_steps:
            errors.append("Default steps must be between 1 and max_steps")
        
        if self.default_guidance <= 0:
            errors.append("Guidance scale must be positive")
        
        # التحقق من إعدادات التخزين
        if self.max_storage_mb <= 0:
            errors.append("Max storage must be positive")
        
        # التحقق من مجلد الإخراج
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
        except Exception as e:
            errors.append(f"Cannot create output directory: {str(e)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """الحصول على ملخص الإعدادات"""
        return {
            "huggingface_configured": bool(self.huggingface_token),
            "default_image_size": f"{self.default_width}x{self.default_height}",
            "max_image_size": f"{self.max_width}x{self.max_height}",
            "default_quality": {
                "steps": self.default_steps,
                "guidance": self.default_guidance
            },
            "storage": {
                "output_dir": self.output_dir,
                "max_storage_mb": self.max_storage_mb,
                "auto_cleanup_days": self.auto_cleanup_days
            },
            "api_limits": {
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "timeout_seconds": self.timeout_seconds
            },
            "features": {
                "watermark": self.enable_watermark,
                "metadata": self.enable_metadata
            }
        }

# إعدادات افتراضية للتطوير
def get_development_config() -> Config:
    """إعدادات للتطوير"""
    return Config(
        default_width=512,
        default_height=512,
        max_width=1024,
        max_height=1024,
        default_steps=20,
        max_steps=30,
        output_dir="output",
        max_storage_mb=500,
        rate_limit_per_minute=5,
        timeout_seconds=30
    )

# إعدادات للإنتاج
def get_production_config() -> Config:
    """إعدادات للإنتاج"""
    return Config(
        default_width=512,
        default_height=512,
        max_width=1024,
        max_height=1024,
        default_steps=25,
        max_steps=50,
        output_dir="output",
        max_storage_mb=2000,
        rate_limit_per_minute=10,
        timeout_seconds=60
    )