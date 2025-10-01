"""
Standardized Error Handling for HaliCred
Provides consistent error responses, classification, and user-friendly messages.
"""

import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .logger import get_logger, get_correlation_id

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    SYSTEM = "system"
    RATE_LIMIT = "rate_limit"
    NOT_FOUND = "not_found"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorDetail:
    """Detailed error information"""
    field: Optional[str] = None
    code: Optional[str] = None
    message: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class StandardError:
    """Standardized error response structure"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    code: str
    message: str
    user_message: str
    details: List[ErrorDetail]
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None
    suggestions: Optional[List[str]] = None


class ErrorHandler:
    """Centralized error handling and response formatting"""

    def __init__(self):
        self.error_mappings = self._initialize_error_mappings()

    def _initialize_error_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Initialize error code mappings with user-friendly messages"""
        return {
            # Authentication errors
            "AUTH_001": {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "message": "Invalid authentication token",
                "user_message": "Your session has expired. Please log in again.",
                "suggestions": ["Refresh the page and log in again", "Clear your browser cache"]
            },
            "AUTH_002": {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "message": "Missing authentication token",
                "user_message": "Please log in to access this feature.",
                "suggestions": ["Click the login button", "Check your internet connection"]
            },
            "AUTH_003": {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "message": "Invalid OTP code",
                "user_message": "The verification code is incorrect or has expired.",
                "suggestions": ["Double-check the code", "Request a new verification code"]
            },

            # Authorization errors
            "AUTHZ_001": {
                "category": ErrorCategory.AUTHORIZATION,
                "severity": ErrorSeverity.MEDIUM,
                "message": "Insufficient permissions",
                "user_message": "You don't have permission to perform this action.",
                "suggestions": ["Contact your administrator for access", "Check your account permissions"]
            },

            # Validation errors
            "VAL_001": {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "message": "Invalid input data",
                "user_message": "Please check your input and try again.",
                "suggestions": ["Review the highlighted fields", "Ensure all required fields are filled"]
            },
            "VAL_002": {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "message": "File upload validation failed",
                "user_message": "The uploaded file is not valid.",
                "suggestions": ["Use a supported file format (JPG, PNG, PDF)", "Ensure file size is under 50MB"]
            },

            # Business logic errors
            "BIZ_001": {
                "category": ErrorCategory.BUSINESS_LOGIC,
                "severity": ErrorSeverity.MEDIUM,
                "message": "GreenScore not available",
                "user_message": "Your sustainability score is not ready yet.",
                "suggestions": ["Upload evidence documents first", "Wait for processing to complete"]
            },
            "BIZ_002": {
                "category": ErrorCategory.BUSINESS_LOGIC,
                "severity": ErrorSeverity.MEDIUM,
                "message": "Loan eligibility requirements not met",
                "user_message": "You don't meet the loan requirements at this time.",
                "suggestions": ["Improve your sustainability score", "Contact our support team"]
            },

            # External service errors
            "EXT_001": {
                "category": ErrorCategory.EXTERNAL_SERVICE,
                "severity": ErrorSeverity.HIGH,
                "message": "External API service unavailable",
                "user_message": "Our processing service is temporarily unavailable.",
                "suggestions": ["Try again in a few minutes", "Contact support if the issue persists"]
            },

            # Database errors
            "DB_001": {
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.CRITICAL,
                "message": "Database connection failed",
                "user_message": "We're experiencing technical difficulties.",
                "suggestions": ["Try again in a few minutes", "Contact support if the issue persists"]
            },

            # System errors
            "SYS_001": {
                "category": ErrorCategory.SYSTEM,
                "severity": ErrorSeverity.CRITICAL,
                "message": "Internal server error",
                "user_message": "Something went wrong on our end.",
                "suggestions": ["Try again in a few minutes", "Contact support with error code"]
            },

            # Rate limiting errors
            "RATE_001": {
                "category": ErrorCategory.RATE_LIMIT,
                "severity": ErrorSeverity.MEDIUM,
                "message": "Rate limit exceeded",
                "user_message": "You're making requests too quickly.",
                "suggestions": ["Wait a moment before trying again", "Reduce the frequency of your requests"]
            },

            # Not found errors
            "NOT_FOUND_001": {
                "category": ErrorCategory.NOT_FOUND,
                "severity": ErrorSeverity.LOW,
                "message": "Resource not found",
                "user_message": "The requested item could not be found.",
                "suggestions": ["Check the URL", "Verify the item exists"]
            }
        }

    def create_error_response(
        self,
        error_code: str,
        details: Optional[List[ErrorDetail]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> StandardError:
        """Create a standardized error response"""
        import uuid
        from datetime import datetime

        error_mapping = self.error_mappings.get(error_code, {
            "category": ErrorCategory.SYSTEM,
            "severity": ErrorSeverity.CRITICAL,
            "message": "Unknown error",
            "user_message": "An unexpected error occurred.",
            "suggestions": ["Try again later", "Contact support"]
        })

        return StandardError(
            error_id=str(uuid.uuid4()),
            category=error_mapping["category"],
            severity=error_mapping["severity"],
            code=error_code,
            message=error_mapping["message"],
            user_message=error_mapping["user_message"],
            details=details or [],
            correlation_id=get_correlation_id(),
            timestamp=datetime.utcnow().isoformat(),
            suggestions=error_mapping.get("suggestions", [])
        )

    def format_error_response(self, error: StandardError) -> Dict[str, Any]:
        """Format error for JSON response"""
        response = {
            "error": {
                "id": error.error_id,
                "code": error.code,
                "message": error.user_message,
                "category": error.category.value,
                "timestamp": error.timestamp,
                "correlation_id": error.correlation_id
            }
        }

        if error.details:
            response["error"]["details"] = [
                {
                    "field": detail.field,
                    "code": detail.code,
                    "message": detail.message,
                    "context": detail.context
                }
                for detail in error.details
                if detail is not None
            ]

        if error.suggestions:
            response["error"]["suggestions"] = error.suggestions

        return response

    def log_error(
        self,
        error: StandardError,
        exception: Optional[Exception] = None,
        request: Optional[Request] = None
    ):
        """Log error with appropriate level based on severity"""
        log_data = {
            "error": {
                "id": error.error_id,
                "code": error.code,
                "category": error.category.value,
                "severity": error.severity.value,
                "message": error.message
            }
        }

        if request:
            log_data["request"] = {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params)
            }

        if exception:
            log_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }

        # Log with appropriate level
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"Error {error.code}: {error.message}", extra_fields=log_data, exception=exception)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Error {error.code}: {error.message}", extra_fields=log_data)
        else:
            logger.info(f"Error {error.code}: {error.message}", extra_fields=log_data)

    def handle_validation_error(self, exc: RequestValidationError) -> StandardError:
        """Handle FastAPI validation errors"""
        details = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            details.append(ErrorDetail(
                field=field_path,
                code="VALIDATION_ERROR",
                message=error["msg"],
                context={"type": error["type"], "input": error.get("input")}
            ))

        return self.create_error_response("VAL_001", details=details)

    def handle_http_exception(self, exc: HTTPException) -> StandardError:
        """Handle HTTP exceptions"""
        error_code_mapping = {
            401: "AUTH_001",
            403: "AUTHZ_001",
            404: "NOT_FOUND_001",
            429: "RATE_001",
            500: "SYS_001"
        }

        error_code = error_code_mapping.get(exc.status_code, "SYS_001")
        return self.create_error_response(error_code)

    def handle_generic_exception(self, exc: Exception) -> StandardError:
        """Handle generic exceptions"""
        return self.create_error_response("SYS_001")





    # Exception handlers for FastAPI
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation exceptions"""
        error = error_handler.handle_validation_error(exc)
        error_handler.log_error(error, exc, request)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_handler.format_error_response(error)
        )


    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        error = error_handler.handle_http_exception(exc)
        error_handler.log_error(error, exc, request)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_handler.format_error_response(error)
        )


    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle generic exceptions"""
        error = error_handler.handle_generic_exception(exc)
        error_handler.log_error(error, exc, request)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_handler.format_error_response(error)
        )


    # Custom exception classes
    class BusinessLogicError(Exception):
        """Business logic error"""
        def __init__(self, error_code: str, message: str = "", context: Dict[str, Any] = None):
            self.error_code = error_code
            self.message = message
            self.context = context or {}
            super().__init__(message)


    class ExternalServiceError(Exception):
        """External service error"""
        def __init__(self, service: str, message: str = "", context: Dict[str, Any] = None):
            self.service = service
            self.message = message
            self.context = context or {}
            super().__init__(f"{service}: {message}")


    class ValidationError(Exception):
        """Validation error"""
        def __init__(self, field: str, message: str = "", context: Dict[str, Any] = None):
            self.field = field
            self.message = message
            self.context = context or {}
            super().__init__(f"{field}: {message}")


    # Utility functions
    def raise_business_error(error_code: str, message: str = "", context: Dict[str, Any] = None):
        """Raise a business logic error"""
        raise BusinessLogicError(error_code, message, context)


    def raise_validation_error(field: str, message: str = "", context: Dict[str, Any] = None):
        """Raise a validation error"""
        raise ValidationError(field, message, context)


    def raise_external_service_error(service: str, message: str = "", context: Dict[str, Any] = None):
        """Raise an external service error"""
        raise ExternalServiceError(service, message, context)


# Global error handler instance
error_handler = ErrorHandler()


# Exception handlers (module level)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )