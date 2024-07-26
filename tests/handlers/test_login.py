from typing import Any
import pytest
from ccproxy.handlers.login import login_handler
from ccproxy.handlers import utils as handler_utils
from ccproxy import model, network, main
from unittest.mock import patch, Mock
import json


class TestLogin:
    @patch('ccproxy.main.authenticate')
    def test_happy_path(self, mock_authenticate: Mock) -> None:
        account_mock = Mock(name='account')
        account_mock.id = '1234'
        mock_authenticate.return_value = account_mock

        payload = {'username': 'un', 'password': 'pwd', 'host': 'https://hst'}

        result = login_handler({'body': json.dumps(payload)}, {})
        mock_authenticate.assert_called_once()
        authenticate_call_args = mock_authenticate.call_args[0]
        assert isinstance(authenticate_call_args[0], model.CredentialsEnvelope)
        assert authenticate_call_args[0].username == payload['username']
        assert authenticate_call_args[0].password == payload['password']
        assert authenticate_call_args[0].host == payload['host']
        assert isinstance(authenticate_call_args[1], main.AccountTable)
        assert 'statusCode' in result
        assert result['statusCode'] == 200
        assert result['body'] == '1234'

    def test_generic_exception_thrown(self) -> None:
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

        payload = {'username': 'un', 'password': 'pwd', 'host': 'https://hst'}

        result = login_handler({'body': json.dumps(payload)}, {})

        assert 'statusCode' in result
        assert result['statusCode'] == 403
        assert 'body' in result
        assert result['body'] == f'Failed to login "un" - "{str(error_type.value)}" error returned.'

        logger.warning.assert_called_once_with(
            'Login error for user "un": Boom'
        )
