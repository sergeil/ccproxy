import json
from typing import Any
from unittest.mock import Mock, patch
import pytest
from requests import Response
from ccproxy import cli, model, tutils
import tempfile


class TestManagingAccountOnRemoteServer:
    def _create_dummy_model(self, json_method_return_value: dict) -> model.Account:
        model = Mock()
        model.json.return_value = json.dumps(json_method_return_value)

        return model

    def _create_dummy_response(self, status_code: int = 200, response_body='{}') -> Response:
        response = Mock()
        response.status_code = status_code
        response.text = response_body

        return response

    @pytest.mark.parametrize(
        'function_name, payload_dict',
        [
            ('create_account_on_server', {'foo': 'bar'}),
            ('update_account_on_server', {'foo': 'bar'})
        ]
    )
    @patch('requests.request')
    def test_happy_path(self, mock_request: Mock, function_name: str, payload_dict: dict[str, Any]):
        payload = self._create_dummy_model(payload_dict)

        acc = tutils.create_account_object()
        acc.id = '1234'
        response_model = model.AccountResponse.from_account(acc)
        response_body = json.loads(response_model.json())
        mock_request.return_value = self._create_dummy_response(response_body=json.dumps(response_body))

        result = getattr(cli, function_name)('foo-url', payload)
        assert isinstance(result, model.AccountResponse)
        assert result.id == '1234'

        mock_request.assert_called_once_with(
            'POST', 
            'foo-url',
            json=payload_dict,
            headers={
                'Content-Type': 'application/json; charset=utf-8',
            }
        )

    @pytest.mark.parametrize(
        'function_name, payload_dict, expected_error',
        [
            ('create_account_on_server', {'foo': 'bar'}, 'Unable to create account, returned error: kaput create'),
            ('update_account_on_server', {'foo': 'bar'}, 'Unable to update account, returned error: kaput update')
        ]
    )
    @patch('requests.request')
    def test_non_200_response_returned(
        self, mock_request: Mock,
        function_name: str,
        payload_dict: dict[str, Any],
        expected_error: str
    ) -> None:
        payload = self._create_dummy_model(payload_dict)

        mock_request.return_value = self._create_dummy_response(500, expected_error)

        with pytest.raises(RuntimeError, match=expected_error):
            getattr(cli, function_name)('foo-url', payload)

        mock_request.assert_called_once()

class TestReadingJsonFile:
    def test_happy_path(self) -> None:
        dict = {'foo': 'bar'}

        with tempfile.NamedTemporaryFile() as file:
            account_json = json.dumps(dict)
            file.write(account_json.encode('utf-8'))
            file.seek(0)

            result = cli._read_json_file(file.name)
            assert result == dict

    def test_file_not_exists(self) -> None:
        with pytest.raises(RuntimeError, match='File "non-existing-file" doesn\'t exist.'):
            cli._read_json_file('non-existing-file')