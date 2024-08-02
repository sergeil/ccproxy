from unittest.mock import Mock
from ccproxy.main import authenticate
from ccproxy import model, network, tutils
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
def test_authenticate_invalid_response(
    mock_do_request: Mock, 
    response: dict[str, Any], 
    expected_exception_type: network.AuthContractError.Types
) -> None:
    dummy_account_table = Mock()

    account = model.Account(
        username='foo-un',
        password='foo-pwd',
        host='https://192.168.1.123:8443',
        config=model.Config(),
        device=tutils.create_account_device_object()
    )

    dummy_response = Mock()
    if 'status_code' in response:
        dummy_response.status_code = response['status_code']

    dummy_response.headers = response['headers'] if 'headers' in response else {}
    dummy_response.json.return_value = {'Status': response['status']} if 'status' in response else {}

    mock_do_request.return_value = dummy_response

    try:
        authenticate(account, dummy_account_table)

        assert False
    except network.AuthContractError as e:
        assert e.type is expected_exception_type


@patch('requests.request')
@patch('ccproxy.network._validate_auth_reponse')
def test_authenticate_happy_path(validate_auth_response: Mock, mock_request: Mock):
    dummy_response = Mock()
    dummy_response.headers = {
        'Set-Cookie': 'abc;def'
    }
    
    mock_request.return_value = dummy_response

    account = model.Account(
        username='un',
        password='pwd',
        host='https://example.com',
        config=model.Config(),
        device=tutils.create_account_device_object()
    )

    authenticated_account = network.authenticate(account)
    assert authenticated_account is not None

    assert mock_request.call_args[0][0] == 'POST'
    assert mock_request.call_args[0][1] == str(account.host) + '/Login'
    payload = mock_request.call_args[1]['json']
    assert isinstance(payload, dict)
    assert payload == {
        'UserName': account.username,
        'Password': account.password,
        'DeviceName': account.device.device_name,
        'OS': account.device.platform,
        'PushToken': account.device.push_token,
        'RememberMe': False
    }
    assert not mock_request.call_args[1]['verify']

    validate_auth_response.assert_called_once()

