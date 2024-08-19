from ccproxy.handlers.update_account import update_account
from unittest.mock import patch, Mock
from ccproxy import tutils
import json
from ccproxy.handlers import utils as handler_utils
import pytest

request_payload = {
    'id': '1234',
    'config': {
        'messages': {
            'foo': ['foo_message']
        },
        'actions': {
            'foo': 'foo_path'
        }
    },
    'device': {
        'device_name': 'updated-dn',
        'push_token': 'updated-pt',
        'platform': 'updated-plt'
    }
}
event = {'body': json.dumps(request_payload)}

class TestUpdateAccount():
    @patch('ccproxy.container.create_account_table')
    def test_happy_path(self, mock_create_account_table: Mock) -> None:
        account_from_db = tutils.create_account_object(override={'id': request_payload['id']})

        mock_account_table = Mock()
        mock_account_table.find.return_value = account_from_db
        mock_account_table.save.return_value = account_from_db

        mock_create_account_table.return_value = mock_account_table

        result = update_account.__wrapped__(event, {})

        assert isinstance(result, dict)
        assert 'statusCode' in result
        assert result['statusCode'] == 200
        assert 'body' in result
        assert 'password' not in result['body']
        expected_keys = ['id', 'config', 'device', 'username', 'host']
        assert len(result['body']) == len(expected_keys)
        for k in expected_keys:
            assert k in result['body']
        assert result['body']['username'] == account_from_db.username
        assert result['body']['host'] == account_from_db.host
        assert result['body']['id'] == account_from_db.id
        assert result['body']['device'] == request_payload['device']
        assert result['body']['config'] == request_payload['config']

        assert len(mock_account_table.find.call_args_list) == 1
        assert mock_account_table.find.call_args_list[0][0][0] == request_payload['id']

        assert len(mock_account_table.save.call_args_list) == 1
        assert mock_account_table.save.call_args_list[0][0][0] == account_from_db

    @patch('ccproxy.container.create_account_table')
    def test_account_not_found(self, mock_create_account_table: Mock) -> None:
        mock_account_table = Mock()
        mock_account_table.find.return_value = None

        mock_create_account_table.return_value = mock_account_table

        with pytest.raises(handler_utils.LambdaHttpError, match=f'Unable to find account with id #{request_payload["id"]}'):
            update_account.__wrapped__(event, {})

    def test_has_exception_handler_decorator(self) -> None:
        assert hasattr(update_account, 'decorators') is True
        assert handler_utils.exception_handler.__name__ in update_account.decorators