from typing import Optional


class AppException(Exception):
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)
    
    def __str__(self):
        return f"[{self.code}] {self.message}"


class ConfigurationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")


class EmbeddingError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "EMBEDDING_ERROR")


class RetrievalError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "RETRIEVAL_ERROR")


class LLMError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")


class AuthenticationError(AppException):
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(AppException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class NotFoundError(AppException):
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource}不存在"
        if resource_id:
            message = f"{resource} (ID: {resource_id}) 不存在"
        super().__init__(message, "NOT_FOUND")


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class DocumentProcessingError(AppException):
    def __init__(self, message: str, filename: Optional[str] = None):
        if filename:
            message = f"文档处理失败 ({filename}): {message}"
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR")


class DatabaseError(AppException):
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")
