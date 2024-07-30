from ccproxy.handlers.update_config import update_config
from unittest.mock import patch, Mock
from ccproxy import model
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
    }
}
event = {'body': json.dumps(request_payload)}

class TestUpdateConfig():
    @patch('ccproxy.container.create_account_table')
    def test_happy_path(self, mock_create_account_table: Mock) -> None:
        account_from_db = model.Account(
            username='foo_username', 
            password='foo_password', 
            host='http://example.org',
            device=model.Device(
                platform='foo-plt',
                push_token='foo-pt',
                device_name='foo-dn'
            )
        )

        mock_account_table = Mock()
        mock_account_table.find.return_value = account_from_db
        mock_account_table.save.return_value = account_from_db

        mock_create_account_table.return_value = mock_account_table

        result = update_config.__wrapped__(event, {})

        assert isinstance(result, dict)
        assert 'statusCode' in result
        assert result['statusCode'] == 200
        assert 'body' in result
        assert result['body'] == request_payload['config']

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
            update_config.__wrapped__(event, {})

    def test_generic_exception_thrown(self) -> None:
        assert hasattr(update_config, 'decorators') is True
        assert handler_utils.exception_handler.__name__ in update_config.decorators