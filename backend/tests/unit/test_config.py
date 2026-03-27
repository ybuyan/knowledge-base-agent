import pytest
from unittest.mock import patch, MagicMock


class TestConfig:
    def test_settings_has_secret_key(self):
        from app.config import settings
        assert hasattr(settings, 'secret_key')
        assert len(settings.secret_key) >= 32
    
    def test_allowed_origins_parsing(self):
        from app.config import settings
        origins = settings.allowed_origins
        assert isinstance(origins, list)
        assert len(origins) > 0
    
    def test_cors_origins_from_env(self, mock_settings):
        with patch('app.config.settings', mock_settings):
            origins = mock_settings.allowed_origins
            assert "http://localhost:3000" in origins


class TestConfigValidation:
    def test_secret_key_length_validation(self):
        from pydantic import ValidationError
        from app.config import Settings
        
        with pytest.raises(ValidationError):
            Settings(secret_key="short")
    
    def test_api_key_min_length(self):
        from pydantic import ValidationError
        from app.config import Settings
        
        with pytest.raises(ValidationError):
            Settings(dashscope_api_key="short")
