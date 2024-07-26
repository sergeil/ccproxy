from typing import Any, Callable, Optional
from logging import Logger
import functools
import json
from pydantic.error_wrappers import ValidationError as PydanticValidationError

class LambdaHttpError(RuntimeError):
    def __init__(self, message, status_code=503, error_type='generic') -> None:
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(message)

class RequestValidationError(LambdaHttpError):
    pass

def extract_body(event: dict[str, Any]) -> dict[str, Any]:
    if 'body' not in event:
        raise LambdaHttpError(
            'This function is meant to be used only with "POST" method.',
            400,
            'no_body_param'
        )

    try:
        body = json.loads(event['body'])
    except Exception:
        raise LambdaHttpError(
            'Body of the request should contain JSON object.',
            400,
            'invalid_json_given'
        )

    if not isinstance(body, dict):
        raise LambdaHttpError(
            'Body of the request should contain JSON object.',
            400,
            'not_object_body_payload'
        )

    return body

def create_http_error_response(error: LambdaHttpError) -> dict[str,  Any]:
    return {
        'statusCode': error.status_code,
        'body': str(error),
        '_errorType': error.error_type,
    }

def create_generic_error_response(error: Exception) -> dict[str,  Any]:
    return {
        'statusCode': 503,
        'body': 'Something went wrong, please check logs'
    }

def create_pydantic_validation_error_response(validation_error: PydanticValidationError):
    validation_errors = {}
    for item in validation_error.errors():
        key = item['loc'][0] # TODO why a tuple?
        if key not in validation_errors:
            validation_errors[key] = []

        validation_errors[key].append({
            'msg': item['msg'],
            'type': item['type']
        })

    return {
        'statusCode': 400,
        'body': {
            'validation_errors': validation_errors
        },
        '_errorType': 'validation_error'
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
            except LambdaHttpError as e:
                return create_http_error_response(e)
            except PydanticValidationError as e:
                return create_pydantic_validation_error_response(e)
            except Exception as e:
                logger.critical(f'Generic exception during login: {str(e)}')
                return create_generic_error_response(e)

        return wrapped_handler

    return decorator
