from unittest.mock import Mock
from ccproxy.main import authenticate
from ccproxy import model, network
from unittest.mock import patch
from typing import Any
import pytest

@pytest.mark.parametrize(
    'response, expected_exception_type',
    [
        (
            {},
            network.AuthContractError.Types.NO_STATUS_FIELD
        ),
        (
            {
                'status': 'not-ok'
            },
            network.AuthContractError.Types.NOT_OK_STATUS
        ),
        (
            {
                'status': 'OK',
                'headers': {}
            },
            network.AuthContractError.Types.NO_COOKIE_HEADER
        )
    ]
)
@patch('ccproxy.network.do_request')
def test_authenticate_invalid_response(mock_do_request: Mock, response: dict[str, Any], expected_exception_type: network.AuthContractError.Types) -> None:
    dummy_account_table = Mock()

    credentials = model.CredentialsEnvelope(
        username='foo-un',
        password='foo-pwd',
        host='https://192.168.1.123:8443'
    )

    dummy_response = Mock()
    if 'status_code' in response:
        dummy_response.status_code = response['status_code']

    dummy_response.headers = response['headers'] if 'headers' in response else {
    }
    dummy_response.json.return_value = {
        'Status': response['status']} if 'status' in response else {}

    mock_do_request.return_value = dummy_response

    try:
        authenticate(credentials, dummy_account_table)

        assert False
    except network.AuthContractError as e:
        assert e.type is expected_exception_type