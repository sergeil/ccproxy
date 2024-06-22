from typing import Any, Callable
from logging import Logger
import functools

def create_generic_error_response(logger: Logger, exception: Exception) -> dict[str,  Any]:
    logger.critical(f'Generic exception during login: {str(exception)}')
    return {
        'statusCode': 503,
        'body': 'Something went wrong, please check logs'
    }


def exception_handler(logger: Logger) -> Callable[..., Any]:
    def decorator(handler_fn: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        if not hasattr(handler_fn, 'decorators'):
            handler_fn.decorators = [] # type: ignore[attr-defined]

         # later used in tests to ensure "exception_handler" decorator is there
        handler_fn.decorators.append(exception_handler.__name__) # type: ignore[attr-defined]

        @functools.wraps(handler_fn)
        def wrapped_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                return handler_fn(*args, **kwargs)
            except Exception as e:
                return create_generic_error_response(logger, e)

        return wrapped_handler

    return decorator
