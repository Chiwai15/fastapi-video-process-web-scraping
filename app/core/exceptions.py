from typing import Any, Dict, Optional, Type, List, Union, Tuple
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    """Error detail model for consistent error responses."""
    loc: Optional[List[str]] = None
    msg: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Error type identifier")
    ctx: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    status_code: int = Field(..., description="HTTP status code")
    error: str = Field(..., description="Error summary")
    details: List[ErrorDetail] = Field(default_factory=list, description="Detailed error information")
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Customize dict output for response."""
        result = super().dict(*args, **kwargs)
        if not result["details"]:
            del result["details"]
        return result


class BaseServiceError(Exception):
    """Base exception for all service-specific errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "service_error"
    error_msg: str = "An internal service error occurred"
    
    def __init__(
        self, 
        message: Optional[str] = None, 
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message or self.error_msg
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.context = context or {}
        super().__init__(self.message)
    
    def to_error_response(self) -> ErrorResponse:
        """Convert exception to standard error response."""
        return ErrorResponse(
            status_code=self.status_code,
            error=self.error_code,
            details=[
                ErrorDetail(
                    msg=self.message,
                    type=self.__class__.__name__,
                    ctx=self.context
                )
            ]
        )


# Specific error types
class NotFoundError(BaseServiceError):
    """Resource not found error."""
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    error_msg = "The requested resource was not found"


class ValidationError(BaseServiceError):
    """Validation error for custom business logic validation."""
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "validation_error"
    error_msg = "Validation error"


class ProcessingError(BaseServiceError):
    """Error during processing a resource."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "processing_error"
    error_msg = "Error processing the request"


class VideoProcessingError(ProcessingError):
    """Specific error for video processing issues."""
    error_code = "video_processing_error"
    error_msg = "Error occurred during video processing"


class ScraperError(ProcessingError):
    """Specific error for web scraping issues."""
    error_code = "scraper_error"
    error_msg = "Error occurred during web scraping"


class CacheError(ProcessingError):
    """Specific error for caching issues."""
    error_code = "cache_error"
    error_msg = "Error with cache operations"