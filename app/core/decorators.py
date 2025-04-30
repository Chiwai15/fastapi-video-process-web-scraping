import functools
import logging
import time
import inspect
from typing import Any, Callable, Dict, Type, TypeVar, Union, cast

from fastapi import HTTPException

F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def error_handler(
    error_map: Dict[Type[Exception], Type[Exception]] = None,
    default_error: Type[Exception] = Exception,
    log_traceback: bool = False
):
    """
    Decorator to handle errors in functions.
    Works with both sync and async functions.
    
    Args:
        error_map: Mapping of source errors to target errors
        default_error: Default error to raise if no mapping found
        log_traceback: Whether to log the traceback
    """
    error_map = error_map or {}
    
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Find matched error in map
                    for error_type, target_error in error_map.items():
                        if isinstance(e, error_type):
                            if log_traceback:
                                logger.exception(f"Error in {func.__name__}: {str(e)}")
                            raise target_error(str(e))
                    
                    # No match, use default
                    if log_traceback:
                        logger.exception(f"Unhandled error in {func.__name__}: {str(e)}")
                    raise default_error(str(e))
            
            return cast(F, async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Find matched error in map
                    for error_type, target_error in error_map.items():
                        if isinstance(e, error_type):
                            if log_traceback:
                                logger.exception(f"Error in {func.__name__}: {str(e)}")
                            raise target_error(str(e))
                    
                    # No match, use default
                    if log_traceback:
                        logger.exception(f"Unhandled error in {func.__name__}: {str(e)}")
                    raise default_error(str(e))
            
            return cast(F, sync_wrapper)
    
    return decorator


def timing_decorator(log_level: int = logging.DEBUG):
    """
    Decorator to log function execution time.
    Works with both sync and async functions.
    
    Args:
        log_level: Logging level for timing info
    """
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    execution_time = end_time - start_time
                    # Get the class name if it's a method
                    if args and hasattr(args[0], '__class__'):
                        class_name = args[0].__class__.__name__
                        func_name = f"{class_name}.{func.__name__}"
                    else:
                        func_name = func.__name__
                    logger.log(log_level, f"{func_name} executed in {execution_time:.4f} seconds")
            
            return cast(F, async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    execution_time = end_time - start_time
                    # Get the class name if it's a method
                    if args and hasattr(args[0], '__class__'):
                        class_name = args[0].__class__.__name__
                        func_name = f"{class_name}.{func.__name__}"
                    else:
                        func_name = func.__name__
                    logger.log(log_level, f"{func_name} executed in {execution_time:.4f} seconds")
            
            return cast(F, sync_wrapper)
    
    return decorator


def api_error_handler():
    """
    Decorator to handle API errors in FastAPI endpoints.
    Converts exceptions to HTTPExceptions.
    Works with both sync and async functions.
    """
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except HTTPException:
                    # Pass through existing HTTPExceptions
                    raise
                except Exception as e:
                    logger.exception(f"API error in {func.__name__}: {str(e)}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            return cast(F, async_wrapper)
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except HTTPException:
                    # Pass through existing HTTPExceptions
                    raise
                except Exception as e:
                    logger.exception(f"API error in {func.__name__}: {str(e)}")
                    raise HTTPException(status_code=500, detail=str(e))
            
            return cast(F, sync_wrapper)
    
    return decorator