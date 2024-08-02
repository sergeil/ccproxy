from unittest.mock import Mock
from ccproxy import tutils, config, container, model, main
from unittest.mock import patch
import uuid
from typing import Any
from decouple import config as read_config
import pytest
import json


# TODO make sure it's working still, this test
@pytest.mark.real_cc_server
def test_authenticate_real() -> None:
    username = read_config('IT_USERNAME')
    password = read_config('IT_PASSWORD')
    host = read_config('IT_HOST')

    saved_account: Any = {}

    account_table_mock = Mock()
    account_table_mock.find_by_host_and_username.return_value = None
    account_table_mock.save.return_value = saved_account

    payload = model.Account(
        username=username,
        password=password,
        host=host
    )
    acc = main.authenticate(payload, account_table_mock)

    account_table_mock.find_by_host_and_username.assert_called_once_with(
        host, username
    )
    account_table_mock.save.assert_called_once()
    save_method_args, _ = account_table_mock.save.call_args_list[0]
    assert len(save_method_args) == 1
    created_acc = save_method_args[0]  # type: model.Account
    assert created_acc.username == username
    assert created_acc.password == password
    assert created_acc.id is None
    assert created_acc.cookie is not None
    assert acc is saved_account


@patch('ccproxy.network.authenticate')
def test_authenticate_new_account_happy_path(mock_network_authenticate: Mock) -> None:
    acc_from_db = {
        'id': 1234
    }

    dummy_account_table = Mock()
    dummy_account_table.save.return_value = acc_from_db

    payload = tutils.create_account_object()

    cookie = 'Token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJTZXNzaW9uSUQiOiI5YTFkOTM1Ny03NmNhLTQzZGQtYTgzOS0xYjk2ZTNkNzAzZmYifQ.qxtE7q5cZREwmc_qb0718i-VKwUnlZ9-3sDxj7EvG2s'

    mock_network_authenticate.return_value = cookie

    auth_acc = main.authenticate(payload, dummy_account_table)

    assert auth_acc is not None
    assert auth_acc == acc_from_db

    dummy_account_table.save.assert_called_once()

    save_method_account = dummy_account_table.save.call_args[0][0]
    assert save_method_account.cookie is cookie
    assert save_method_account.config is payload.config
    assert save_method_account.password is payload.password
    assert auth_acc['id'] == acc_from_db['id'] # type: ignore[index]

@patch('ccproxy.network.authenticate')
def test_authenticate_existing_account(mock_network_authenticate: Mock) -> None:
    acc_from_db = tutils.create_account_object(
        override={
            'password': 'db-password'
        },
        config_override={
            'device_name': 'db-dn',
            'push_token': 'db-pt',
            'platform': 'db-plt'
        }
    )

    dummy_account_table = Mock()
    dummy_account_table.find.return_value = acc_from_db
    dummy_account_table.save.return_value = acc_from_db

    payload = tutils.create_account_object()

    cookie = 'Token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJTZXNzaW9uSUQiOiI5YTFkOTM1Ny03NmNhLTQzZGQtYTgzOS0xYjk2ZTNkNzAzZmYifQ.qxtE7q5cZREwmc_qb0718i-VKwUnlZ9-3sDxj7EvG2s'

    mock_network_authenticate.return_value = cookie

    auth_acc = main.authenticate(payload, dummy_account_table)
    assert auth_acc is acc_from_db

    dummy_account_table.save.assert_called_once()

    save_method_account = dummy_account_table.save.call_args[0][0]
    assert save_method_account.cookie is cookie
    assert save_method_account.password is payload.password
    assert save_method_account.config is payload.config
    assert save_method_account.device is payload.device
    assert auth_acc.id == acc_from_db.id # type: ignore[index]

def create_pe_mock() -> Mock:
    def encrypt(input: str) -> str:
        return f'{input}-encrypted'

    def decrypt(input: str) -> str:
        return f'{input}-decrypted'

    mock = Mock()
    mock.encrypt.side_effect = encrypt
    mock.decrypt.side_effect = decrypt

    return mock


class TestAccountTable:
    def test_save(self) -> None:
        tutils.create_accounts_table_if_not_exists()

        dynamodb = container.create_dynamodb_resource()
        at = main.AccountTable(create_pe_mock(), dynamodb)
        raw_table = dynamodb.Table(config.ACCOUNTS_TABLE)

        acc = tutils.create_account_object()

        saved_acc = at.save(acc)  # save
        assert saved_acc is not None
        assert saved_acc.id is not None
        assert saved_acc.username == acc.username
        assert saved_acc.password == acc.password
        assert saved_acc.host == acc.host
        assert saved_acc.cookie == acc.cookie
        assert saved_acc.config is acc.config
        assert saved_acc.device is acc.device

        raw_saved_account = raw_table.get_item(Key={'id': saved_acc.id})
        assert 'Item' in raw_saved_account
        raw_saved_account = raw_saved_account['Item']
        assert 'id' in raw_saved_account
        assert raw_saved_account['id'] == saved_acc.id
        assert 'username' in raw_saved_account
        assert raw_saved_account['username'] == saved_acc.username
        assert 'password' in raw_saved_account
        assert raw_saved_account['password'] == 'foo-password-encrypted'
        assert 'host' in raw_saved_account
        assert raw_saved_account['host'] == saved_acc.host
        assert 'cookie' in raw_saved_account
        assert raw_saved_account['cookie'] == 'foo-cookie-encrypted'
        assert 'config' in raw_saved_account
        assert raw_saved_account['config'] is not None
        assert 'messages' in raw_saved_account['config']
        assert raw_saved_account['config']['messages'] == acc.config.messages
        assert 'actions' in raw_saved_account['config']
        assert raw_saved_account['config']['actions'] == acc.config.actions
        assert 'device' in raw_saved_account
        assert json.loads(acc.device.json()) == raw_saved_account['device']

        # veryfing "update" for a managed entity:

        saved_acc.username = 'updated-username'
        saved_acc.password = 'updated-password'
        saved_acc.host = 'updated-host'
        saved_acc.cookie = 'updated-cookie'
        saved_acc.config = model.Config(
            messages={'bar_action': ['bar_msg1']},
            actions={'bar_action': 'bar_action_path'}
        )
        saved_acc.device.device_name = 'updated-dn'
        saved_acc.device.platform = 'updated-plt'
        saved_acc.device.push_token = 'updated-pt'

        updated_acc = at.save(saved_acc)  # update
        assert updated_acc is not None
        assert updated_acc.username == 'updated-username'
        assert updated_acc.password == 'updated-password'
        assert updated_acc.host == 'updated-host'
        assert updated_acc.cookie == 'updated-cookie'
        assert updated_acc.config is not None
        assert updated_acc.config.actions == saved_acc.config.actions
        assert updated_acc.config.messages == saved_acc.config.messages
        assert updated_acc.device is not None
        assert updated_acc.device.device_name == 'updated-dn'
        assert updated_acc.device.platform == 'updated-plt'
        assert updated_acc.device.push_token == 'updated-pt'

        raw_updated_account = raw_table.get_item(Key={'id': updated_acc.id})
        assert 'Item' in raw_updated_account
        raw_updated_account = raw_updated_account['Item']
        assert raw_updated_account['username'] == 'updated-username'
        assert raw_updated_account['password'] == 'updated-password-encrypted'
        assert raw_updated_account['host'] == 'updated-host'
        assert raw_updated_account['cookie'] == 'updated-cookie-encrypted'
        assert 'config' in raw_updated_account
        assert raw_updated_account['config']['actions'] == saved_acc.config.actions
        assert raw_updated_account['config']['messages'] == saved_acc.config.messages
        assert 'device' in raw_updated_account
        assert raw_updated_account['device']['device_name'] == 'updated-dn'
        assert raw_updated_account['device']['platform'] == 'updated-plt'
        assert raw_updated_account['device']['push_token'] == 'updated-pt'

    def test_find(self) -> None:
        tutils.create_accounts_table_if_not_exists()

        pe = create_pe_mock()
        dynamodb = container.create_dynamodb_resource()
        at = main.AccountTable(pe, dynamodb)
        raw_table = dynamodb.Table(config.ACCOUNTS_TABLE)

        id = str(uuid.uuid4())[:8]
        item = {
            'id': id,
            'username': 'un',
            'password': 'pwd',
            'host': 'https://hst',
            'cookie': 'ck',
            'config': {
                'messages': {
                    'foo_action': ['msg1', 'msg2']
                },
                'actions': {
                    'foo_action': 'foo_path'
                }
            },
            'device': {
                'platform': 'foo-plt',
                'device_name': 'foo-dn',
                'push_token': 'foo-pt'
            }
        }

        raw_table.put_item(Item=item)

        fetched_account = at.find(id)
        assert fetched_account is not None
        assert fetched_account.id == id
        assert fetched_account.username == 'un'
        assert fetched_account.password == 'pwd-decrypted'
        assert fetched_account.host == 'https://hst'
        assert fetched_account.cookie == 'ck-decrypted'
        assert fetched_account.config is not None
        assert fetched_account.config.actions == item['config']['actions']
        assert fetched_account.config.messages == item['config']['messages']
        assert fetched_account.device is not None
        assert fetched_account.device.platform == item['device']['platform']
        assert fetched_account.device.device_name == item['device']['device_name']
        assert fetched_account.device.push_token == item['device']['push_token']

        non_existing_account = at.find('non existing id')
        assert non_existing_account is None
        assert pe.encrypt.call_count == 0
        assert pe.decrypt.call_count == 2

    def test_find_by_host_and_username(self) -> None:
        tutils.create_accounts_table_if_not_exists()

        pe = create_pe_mock()
        dynamodb = container.create_dynamodb_resource()
        at = main.AccountTable(pe, dynamodb)
        raw_table = dynamodb.Table(config.ACCOUNTS_TABLE)

        username = f'foo-un{uuid.uuid4()}'
        host = f'https://foo-hst{uuid.uuid4()}'

        id = str(uuid.uuid4())[:8]
        item = {
            'id': id,
            'username': username,
            'host': host,
            'password': 'foo-pwd',
            'cookie': 'foo-ck',
            'device': {
                'platform': 'foo-plt',
                'device_name': 'foo-dn',
                'push_token': 'foo-pt'
            },
            'config': {}
        }

        empty_result = at.find_by_host_and_username(host, username)
        assert empty_result is None

        raw_table.put_item(
            Item=item
        )
        account = at.find_by_host_and_username(host, username)
        assert account is not None
        assert account.username == username
        assert account.host == host
        assert account.password == 'foo-pwd-decrypted'
        assert account.cookie == 'foo-ck-decrypted'
        assert account.id == id
        assert account.device is not None
        assert account.device.platform == item['device']['platform']
        assert account.device.device_name == item['device']['device_name']
        assert account.device.push_token == item['device']['push_token']
        assert pe.encrypt.call_count == 0
        assert pe.decrypt.call_count == 2


def test_encrypter() -> None:
    enc = main.Encrypter()

    original = 'foobar'

    encrypted = enc.encrypt(original)
    assert encrypted is not None

    decrypted = enc.decrypt(encrypted)
    assert decrypted == original
