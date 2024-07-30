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

    # TODO consider externalising dummy account creation in utility method
    payload = model.Account(
        username='foo-un',
        password='foo-pwd',
        host='https://192.168.1.123:8443',
        config=model.Config(
            messages ={'foo_action': ['foo_msg1', 'foo_msg2']}
        ),
        device=model.Device(
            device_name='dn', 
            platform='iOS', 
            push_token='pt'
        )
    )

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
    device_def = {
        'device_name': 'dn', 
        'platform': 'iOS', 
        'push_token': 'pt'
    }

    acc_from_db = model.Account(
        id='foo-id',
        username='foo-username',
        password='foo-password',
        host='https://example.org',
        device=model.Device(**device_def)
    )

    dummy_account_table = Mock()
    dummy_account_table.find.return_value = acc_from_db
    dummy_account_table.save.return_value = acc_from_db

    # TODO consider externalising dummy account creation in utility method
    payload = model.Account(
        username='foo-un',
        password='foo-pwd',
        host='https://192.168.1.123:8443',
        config=model.Config(
            messages ={'foo_action': ['foo_msg1', 'foo_msg2']}
        ),
        device=model.Device(**device_def)
    )

    cookie = 'Token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJTZXNzaW9uSUQiOiI5YTFkOTM1Ny03NmNhLTQzZGQtYTgzOS0xYjk2ZTNkNzAzZmYifQ.qxtE7q5cZREwmc_qb0718i-VKwUnlZ9-3sDxj7EvG2s'

    mock_network_authenticate.return_value = cookie

    auth_acc = main.authenticate(payload, dummy_account_table)
    assert auth_acc is acc_from_db

    dummy_account_table.save.assert_called_once()

    save_method_account = dummy_account_table.save.call_args[0][0]
    assert save_method_account.cookie is cookie
    assert save_method_account.config is payload.config
    assert save_method_account.password is payload.password
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
    def _create_config(self) -> model.Config:
        acc_config_messages = {'foo_action': ['foo_msg', 'bar_msg']}
        acc_config_actions = {'foo_action': 'foo_path'}

        return model.Config(
            messages=acc_config_messages,
            actions=acc_config_actions
        )
    
    def _create_device(self) -> model.Device:
        return model.Device(
            device_name='foo-dn',
            platform='foo-pl',
            push_token='foo-pt'
        )

    def test_save(self) -> None:
        tutils.create_accounts_table_if_not_exists()

        dynamodb = container.create_dynamodb_resource()
        at = main.AccountTable(create_pe_mock(), dynamodb)
        raw_table = dynamodb.Table(config.ACCOUNTS_TABLE)

        account_config = self._create_config()
        device = self._create_device()

        acc = model.Account(
            username='un',
            password='pwd',
            host='https://hst',
            cookie='ck',
            config=account_config,
            device=device
        )

        saved_acc = at.save(acc)  # save
        assert saved_acc is not None
        assert saved_acc.id is not None
        assert saved_acc.username == 'un'
        assert saved_acc.password == 'pwd'
        assert saved_acc.host == 'https://hst'
        assert saved_acc.cookie == 'ck'
        assert saved_acc.config is not None
        assert saved_acc.device is not None

        raw_saved_account = raw_table.get_item(Key={'id': saved_acc.id})
        assert 'Item' in raw_saved_account
        raw_saved_account = raw_saved_account['Item']
        assert 'id' in raw_saved_account
        assert raw_saved_account['id'] == saved_acc.id
        assert 'username' in raw_saved_account
        assert raw_saved_account['username'] == saved_acc.username
        assert 'password' in raw_saved_account
        assert raw_saved_account['password'] == 'pwd-encrypted'
        assert 'host' in raw_saved_account
        assert raw_saved_account['host'] == saved_acc.host
        assert 'cookie' in raw_saved_account
        assert raw_saved_account['cookie'] == 'ck-encrypted'
        assert 'config' in raw_saved_account
        assert raw_saved_account['config'] is not None
        assert 'messages' in raw_saved_account['config']
        assert raw_saved_account['config']['messages'] == account_config.messages
        assert 'actions' in raw_saved_account['config']
        assert raw_saved_account['config']['actions'] == account_config.actions
        assert 'device' in raw_saved_account
        assert 'device_name' in raw_saved_account['device']
        assert json.loads(device.json()) == raw_saved_account['device']

        saved_acc.username = 'foo-un'
        saved_acc.password = 'foo-pwd'
        saved_acc.host = 'foo-hst'
        saved_acc.cookie = 'foo-ck'
        saved_acc.config = model.Config(
            messages={'bar_action': ['bar_msg1']}, actions={'bar_action': 'bar_action_path'}
        )
        saved_acc.device.device_name = 'updated-dn'
        saved_acc.device.platform = 'updated-plt'
        saved_acc.device.push_token = 'updated-pt'

        updated_acc = at.save(saved_acc)  # update
        assert updated_acc is not None
        assert updated_acc.username == 'foo-un'
        assert updated_acc.password == 'foo-pwd'
        assert updated_acc.host == 'foo-hst'
        assert updated_acc.cookie == 'foo-ck'
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
        assert raw_updated_account['username'] == 'foo-un'
        assert raw_updated_account['password'] == 'foo-pwd-encrypted'
        assert raw_updated_account['host'] == 'foo-hst'
        assert raw_updated_account['cookie'] == 'foo-ck-encrypted'
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

        raw_table.put_item(
            Item=item
        )

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
            }
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
