import ccproxy.handlers.utils as handlers_utils
from unittest.mock import Mock, patch
from typing import Any
import pytest
from pydantic import BaseModel, Field
from pydantic.error_wrappers import ValidationError as PydanticValidationError

class FooModel(BaseModel):
    username: str
    password: str = Field(min_length=1)


def test_create_generic_error_response() -> None:
    e = Exception('Boom!')

    result = handlers_utils.create_generic_error_response(e)

    assert 'statusCode' in result
    assert result['statusCode'] == 503
    assert 'body' in result
    assert result['body'] == 'Something went wrong, please check logs'

def test_create_http_error_response() -> None:
    e = handlers_utils.LambdaHttpError('Not found!', 404, 'not_found')

    result = handlers_utils.create_http_error_response(e)

    assert 'statusCode' in result
    assert result['statusCode'] == 404
    assert 'body' in result
    assert result['body'] == 'Not found!'
    assert '_errorType' in result
    assert result['_errorType'] == 'not_found'

def test_create_pydantic_validation_error_response() -> None:
    thrown_error = None

    try:
        FooModel()
    except PydanticValidationError as e:
        thrown_error = e

    assert thrown_error is not None

    response = handlers_utils.create_pydantic_validation_error_response(thrown_error)
    assert isinstance(response, dict)
    assert 'statusCode' in response
    assert response['statusCode'] == 400
    assert 'body' in response
    assert 'validation_errors' in response['body']
    assert response['body']['validation_errors'] == {
        'username': [{'msg': 'field required', 'type': 'value_error.missing'}],
        'password': [{'msg': 'field required', 'type': 'value_error.missing'}]
    }

@patch('ccproxy.handlers.utils.create_generic_error_response')
def test_decorator_generic(mock_create_generic_error_response) -> None:
    mock_logger = Mock()
    _test_decorator(
        Exception('Boom!'), 
        mock_create_generic_error_response,
        mock_logger
    )

    mock_logger.critical.assert_called_once_with(
        'Generic exception during login: Boom!'
    )

@patch('ccproxy.handlers.utils.create_http_error_response')
def test_decorator_http_code(mock_create_http_error_response) -> None:
    _test_decorator(
        handlers_utils.LambdaHttpError('Boom'), 
        mock_create_http_error_response
    )

@patch('ccproxy.handlers.utils.create_pydantic_validation_error_response')
def test_decorator_pydantic_validation(mock_create_pydantic_validation_error_response) -> None:
    try:
        FooModel()
    except PydanticValidationError as e:
        _test_decorator(e,  mock_create_pydantic_validation_error_response)


def _test_decorator(error: Exception, mock_method: Mock, logger=Mock()) -> None:
    dummy_response = {}

    mock_method.return_value = dummy_response

    @handlers_utils.exception_handler(logger=logger)
    def throw_exception() -> None:
        raise error

    result = throw_exception()

    assert result is dummy_response
    assert mock_method.call_args[0][0] is error

@pytest.mark.parametrize(
    'event, expected_error_type',
    [
        ({}, 'no_body_param'),
        ({'body': 'bla'}, 'invalid_json_given'),
        ({'body': '"bla"'}, 'not_object_body_payload')
    ]
)
def test_extract_body_errors(event: dict[str, Any], expected_error_type: str) -> None:
    thrown_error = None

    try:
        result = handlers_utils.extract_body(event)
    except handlers_utils.LambdaHttpError as e:
        thrown_error = e

    assert thrown_error is not None
    assert thrown_error.status_code == 400
    assert thrown_error.error_type == expected_error_type

def test_extract_body_happy_path() -> None:
    result = handlers_utils.extract_body({'body': '{"foo": "bar"}'})

    assert 'foo' in result
    assert result['foo'] == 'bar'
