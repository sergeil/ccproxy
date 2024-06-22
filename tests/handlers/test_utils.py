from ccproxy.handlers.utils import create_generic_error_response, exception_handler
from unittest.mock import Mock


def test_create_generic_error_response() -> None:
    mock_logger = Mock()
    e = Exception('Boom!')

    result = create_generic_error_response(mock_logger, e)

    assert result['statusCode'] == 503
    assert 'body' in result
    assert result['body'] == 'Something went wrong, please check logs'

    mock_logger.critical.assert_called_once_with(
        'Generic exception during login: Boom!'
    )


def test_decorator() -> None:
    logger = Mock()

    @exception_handler(logger=logger)
    def throw_exception() -> None:
        raise Exception('Boom')

    result = throw_exception()

    assert 'statusCode' in result
    assert result['statusCode'] == 503
    assert 'body' in result
    assert result['body'] == 'Something went wrong, please check logs'

    logger.critical.assert_called_once_with(
        'Generic exception during login: Boom'
    )
