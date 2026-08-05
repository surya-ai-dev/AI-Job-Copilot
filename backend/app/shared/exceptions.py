# backend/app/shared/exceptions.py
# Clean Architecture application exceptions

class BaseAppException(Exception):
    """Base exception class for all custom application errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class ValidationException(BaseAppException):
    """Raised when request payload or file validation fails."""
    def __init__(self, message: str, details: list = None):
        super().__init__(message, code="VALIDATION_ERROR")
        self.details = details or []


class BusinessRuleException(BaseAppException):
    """Raised when actions violate business rule invariants."""
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(message, code)


class AuthenticationException(BaseAppException):
    """Raised during login, registration, or token validation errors."""
    def __init__(self, message: str, code: str = "AUTHENTICATION_ERROR"):
        super().__init__(message, code)


class NotFoundException(BaseAppException):
    """Raised when a requested resource is missing in the database."""
    def __init__(self, message: str, code: str = "NOT_FOUND"):
        super().__init__(message, code)
