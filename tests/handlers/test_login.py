import pytest
from ccproxy.handlers.login import login_handler
from ccproxy.handlers import utils as handler_utils
from ccproxy import model, network, main, tutils
from unittest.mock import patch, Mock
import json


login_payload = {
    'username': 'un',
    'password': 'pwd',
    'host': 'https://hst',
    'device': {
        'device_name': 'foo-device',
        'platform': 'iOS',
        'push_token': '1234pt'
    },
    'config': {
    }
}

class TestLogin:
    @patch('ccproxy.main.authenticate')
    def test_happy_path(self, mock_authenticate_fn: Mock) -> None:
        account_to_auth = tutils.create_account_object(login_payload)
        account_to_auth.id = '1234'
        mock_authenticate_fn.return_value = account_to_auth

        response = login_handler.__wrapped__({'body': json.dumps(login_payload)}, {})
        mock_authenticate_fn.assert_called_once()
        authenticate_call_args = mock_authenticate_fn.call_args[0]
        assert isinstance(authenticate_call_args[0], model.CredentialsEnvelope)
        assert authenticate_call_args[0].username == login_payload['username']
        assert authenticate_call_args[0].password == login_payload['password']
        assert authenticate_call_args[0].host == login_payload['host']
        assert isinstance(authenticate_call_args[1], main.AccountTable)
        assert 'statusCode' in response
        assert response['statusCode'] == 200
        assert 'body' in response
        assert isinstance(response['body'], dict)
        for k in ['id', 'config', 'username', 'config', 'device']:
            assert k in response['body']
        assert response['body']['id'] == account_to_auth.id

    def test_has_exception_handler_decorator(self) -> None:
        assert hasattr(login_handler, 'decorators') is True
        assert handler_utils.exception_handler.__name__ in login_handler.decorators

    @pytest.mark.parametrize(
        'error_type',
        [e for e in network.AuthContractError.Types]
    )
    @patch('ccproxy.main.authenticate')
    @patch('ccproxy.handlers.login.logger')
    def test_auth_error(self, logger: Mock, mock_authenticate: Mock, error_type: network.AuthContractError.Types) -> None:
        mock_authenticate.side_effect = network.AuthContractError(
            'Boom', type=error_type)

        result = login_handler({'body': json.dumps(login_payload)}, {})

        assert 'statusCode' in result
        assert result['statusCode'] == 403
        assert 'body' in result
        assert result['body'] == f'Failed to login "un" - "{str(error_type.value)}" error returned.'

        logger.warning.assert_called_once_with(
            'Login error for user "un": Boom'
        )
