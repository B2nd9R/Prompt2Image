import pytest
import asyncio
import os
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json

from main import app
from image_generator import ImageGenerator
from utils.config import Config
from utils.save_image import ImageSaver

# إنشاء عميل الاختبار
client = TestClient(app)

class TestPrompt2ImageAPI:
    """اختبارات API الرئيسي"""
    
    def test_root_endpoint(self):
        """اختبار الصفحة الرئيسية"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
    
    def test_health_endpoint(self):
        """اختبار endpoint الصحة"""
        with patch('main.image_generator') as mock_generator:
            mock_generator.test_connection.return_value = True
            response = client.get("/health")
            assert response.status_code == 200
    
    @patch('main.image_generator.generate_image')
    @patch('main.image_saver.save_image')
    def test_generate_image_success(self, mock_save, mock_generate):
        """اختبار توليد صورة بنجاح"""
        # تحضير البيانات الوهمية
        mock_generate.return_value = b"fake_image_data"
        mock_save.return_value = "test_image.png"
        
        # إرسال طلب توليد صورة
        response = client.post("/generate", json={
            "prompt": "A beautiful sunset",
            "width": 512,
            "height": 512
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "image_url" in data
        assert "filename" in data
    
    def test_generate_image_invalid_prompt(self):
        """اختبار توليد صورة بوصف غير صالح"""
        response = client.post("/generate", json={
            "prompt": "",  # وصف فارغ
            "width": 512,
            "height": 512
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_generate_image_invalid_dimensions(self):
        """اختبار توليد صورة بأبعاد غير صالحة"""
        response = client.post("/generate", json={
            "prompt": "Test prompt",
            "width": -1,  # عرض سالب
            "height": 512
        })
        
        assert response.status_code == 422
    
    def test_gallery_endpoint(self):
        """اختبار endpoint المعرض"""
        with patch('os.path.exists') as mock_exists:
            with patch('os.listdir') as mock_listdir:
                with patch('os.stat') as mock_stat:
                    mock_exists.return_value = True
                    mock_listdir.return_value = ["test.png", "test2.jpg"]
                    mock_stat.return_value.st_ctime = 1640995200  # timestamp
                    mock_stat.return_value.st_size = 1024
                    
                    response = client.get("/gallery")
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert "images" in data
    
    def test_stats_endpoint(self):
        """اختبار endpoint الإحصائيات"""
        with patch('os.path.exists') as mock_exists:
            with patch('os.listdir') as mock_listdir:
                with patch('os.path.getsize') as mock_getsize:
                    mock_exists.return_value = True
                    mock_listdir.return_value = ["test.png"]
                    mock_getsize.return_value = 1024 * 1024  # 1MB
                    
                    response = client.get("/stats")
                    assert response.status_code == 200
                    data = response.json()
                    assert "total_images" in data
                    assert "total_size_mb" in data
    
    def test_delete_image_success(self):
        """اختبار حذف صورة بنجاح"""
        with patch('os.path.exists') as mock_exists:
            with patch('os.remove') as mock_remove:
                mock_exists.return_value = True
                
                response = client.delete("/image/test.png")
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
    
    def test_delete_image_not_found(self):
        """اختبار حذف صورة غير موجودة"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            response = client.delete("/image/nonexistent.png")
            assert response.status_code == 404

class TestImageGenerator:
    """اختبارات مولد الصور"""
    
    def setup_method(self):
        """إعداد الاختبارات"""
        self.config = Config()
        self.config.huggingface_token = "test_token"
        self.generator = ImageGenerator(self.config)
    
    def test_init(self):
        """اختبار تهيئة المولد"""
        assert self.generator.config == self.config
        assert self.generator.api_url is not None
        assert "Authorization" in self.generator.headers
    
    def test_enhance_prompt(self):
        """اختبار تحسين الوصف"""
        original_prompt = "A cat"
        enhanced = self.generator._enhance_prompt(original_prompt)
        
        assert len(enhanced) > len(original_prompt)
        assert "high quality" in enhanced
    
    def test_add_variation(self):
        """اختبار إضافة تنويع للوصف"""
        original_prompt = "A dog"
        varied = self.generator._add_variation(original_prompt, 0)
        
        assert len(varied) > len(original_prompt)
        assert original_prompt in varied
    
    def test_get_available_models(self):
        """اختبار الحصول على النماذج المتاحة"""
        models = self.generator.get_available_models()
        
        assert isinstance(models, dict)
        assert len(models) > 0
        assert "stable-diffusion-xl" in models
    
    @pytest.mark.asyncio
    async def test_validate_image_success(self):
        """اختبار التحقق من صحة الصورة"""
        # إنشاء صورة وهمية صالحة
        from PIL import Image
        import io
        
        img = Image.new('RGB', (512, 512), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        is_valid = await self.generator._validate_image(img_data)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_image_invalid(self):
        """اختبار التحقق من صورة غير صالحة"""
        invalid_data = b"not_an_image"
        
        is_valid = await self.generator._validate_image(invalid_data)
        assert is_valid is False

class TestImageSaver:
    """اختبارات حافظ الصور"""
    
    def setup_method(self):
        """إعداد الاختبارات"""
        self.temp_dir = tempfile.mkdtemp()
        self.saver = ImageSaver(self.temp_dir)
    
    def teardown_method(self):
        """تنظيف الاختبارات"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """اختبار تهيئة الحافظ"""
        assert self.saver.output_dir == self.temp_dir
        assert os.path.exists(self.temp_dir)
    
    def test_generate_filename(self):
        """اختبار توليد اسم الملف"""
        prompt = "A beautiful sunset over mountains"
        image_id = "test-id-123"
        
        filename = self.saver._generate_filename(prompt, image_id)
        
        assert filename.endswith('.png')
        assert 'sunset' in filename.lower()
        assert 'test-id-123'[:8] in filename
    
    def test_generate_filename_special_chars(self):
        """اختبار توليد اسم ملف مع أحرف خاصة"""
        prompt = "A cat & dog! @#$%"
        image_id = "test-id-456"
        
        filename = self.saver._generate_filename(prompt, image_id)
        
        # التأكد من عدم وجود أحرف خاصة
        assert '&' not in filename
        assert '!' not in filename
        assert '@' not in filename
    
    @pytest.mark.asyncio
    async def test_save_image_success(self):
        """اختبار حفظ صورة بنجاح"""
        # إنشاء صورة وهمية
        from PIL import Image
        import io
        
        img = Image.new('RGB', (512, 512), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # حفظ الصورة
        filename = await self.saver.save_image(
            image_data=img_data,
            prompt="Test prompt",
            image_id="test-123"
        )
        
        assert filename is not None
        assert filename.endswith('.png')
        assert os.path.exists(os.path.join(self.temp_dir, filename))
    
    def test_get_storage_info(self):
        """اختبار معلومات التخزين"""
        # إنشاء ملف وهمي
        test_file = os.path.join(self.temp_dir, "test.png")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        storage_info = self.saver.get_storage_info()
        
        assert "total_files" in storage_info
        assert storage_info["total_files"] >= 1
        assert "total_size_mb" in storage_info
    
    def test_delete_image_success(self):
        """اختبار حذف صورة بنجاح"""
        # إضافة بيانات وهمية
        self.saver.metadata["test-id"] = {
            "filename": "test.png",
            "prompt": "Test",
            "image_id": "test-id"
        }
        
        # إنشاء الملف
        test_file = os.path.join(self.temp_dir, "test.png")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # حذف الصورة
        success = self.saver.delete_image("test-id")
        
        assert success is True
        assert "test-id" not in self.saver.metadata
        assert not os.path.exists(test_file)
    
    def test_cleanup_old_images(self):
        """اختبار تنظيف الصور القديمة"""
        # إضافة بيانات وهمية قديمة
        from datetime import datetime, timedelta
        
        old_date = (datetime.now() - timedelta(days=35)).isoformat()
        self.saver.metadata["old-id"] = {
            "filename": "old.png",
            "created_at": old_date,
            "image_id": "old-id"
        }
        
        # إنشاء الملف
        old_file = os.path.join(self.temp_dir, "old.png")
        with open(old_file, 'w') as f:
            f.write("old content")
        
        # تنظيف الصور القديمة
        deleted_count = self.saver.cleanup_old_images(days_old=30)
        
        assert deleted_count >= 1
        assert "old-id" not in self.saver.metadata

class TestConfig:
    """اختبارات الإعدادات"""
    
    def test_config_init(self):
        """اختبار تهيئة الإعدادات"""
        config = Config()
        
        assert config.default_width == 512
        assert config.default_height == 512
        assert config.output_dir == "output"
    
    def test_config_validation_success(self):
        """اختبار التحقق من صحة الإعدادات"""
        config = Config()
        config.huggingface_token = "test_token"
        
        validation = config.validate()
        
        assert validation["valid"] is True
        assert len(validation["errors"]) == 0
    
    def test_config_validation_missing_token(self):
        """اختبار التحقق من إعدادات بدون توكن"""
        config = Config()
        config.huggingface_token = None
        
        validation = config.validate()
        
        assert validation["valid"] is False
        assert any("token" in error.lower() for error in validation["errors"])
    
    def test_config_summary(self):
        """اختبار ملخص الإعدادات"""
        config = Config()
        config.huggingface_token = "test_token"
        
        summary = config.get_summary()
        
        assert "huggingface_configured" in summary
        assert "default_image_size" in summary
        assert "storage" in summary
    
    def test_config_save_load(self):
        """اختبار حفظ وتحميل الإعدادات"""
        config = Config()
        config.default_width = 1024
        
        # حفظ في ملف مؤقت
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.close()
        
        try:
            config.save_to_file(temp_file.name)
            
            # إنشاء إعدادات جديدة وتحميلها
            new_config = Config()
            new_config.load_from_file(temp_file.name)
            
            assert new_config.default_width == 1024
            
        finally:
            os.unlink(temp_file.name)

# اختبارات التكامل
class TestIntegration:
    """اختبارات التكامل"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """اختبار سير العمل الكامل"""
        # هذا اختبار تكامل يتطلب API فعلي
        # يمكن تخطيه في البيئة العادية
        pytest.skip("Integration test requires actual API")
    
    def test_error_handling(self):
        """اختبار معالجة الأخطاء"""
        # اختبار معالجة الأخطاء في النظام
        with patch('main.image_generator.generate_image') as mock_generate:
            mock_generate.side_effect = Exception("Test error")
            
            response = client.post("/generate", json={
                "prompt": "Test prompt"
            })
            
            assert response.status_code == 500

# إعدادات pytest
def pytest_configure(config):
    """إعداد pytest"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])