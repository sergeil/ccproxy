import uuid
from typing import Optional, Any
from ccproxy import config
from boto3.dynamodb.conditions import Key, Attr
from cryptography.fernet import Fernet
from mypy_boto3_dynamodb import DynamoDBServiceResource
from ccproxy import model, network
import json


class Encrypter:
    def __init__(self) -> None:
        self._fernet = Fernet(bytes(config.DB_ENCRYPTION_KEY, 'utf-8'))

    def encrypt(self, raw_password: str) -> str:
        return self._fernet.encrypt(bytes(raw_password, 'utf-8')).decode('utf-8')

    def decrypt(self, encrypted_password: str) -> str:
        return self._fernet.decrypt(bytes(encrypted_password, 'utf-8')).decode('utf-8')


class AccountTable:
    def __init__(self, encrypter: Encrypter, dynamodb_resource: DynamoDBServiceResource):
        # TODO prolly better jus to pass a Table to constructor?
        self._table = dynamodb_resource.Table(config.ACCOUNTS_TABLE)
        self._encrypter = encrypter

    def save(self, account: model.Account) -> model.Account:
        if account.cookie is None:
            raise RuntimeError(f"model.cookie cannot be None (but for Account with username '{account.username}' it is)")

        encrypted_password = self._encrypter.encrypt(account.password)
        encrypted_cookie = self._encrypter.encrypt(account.cookie)

        # TODO consider introducing a fn that would prepare an arg for put_item()

        if account.id is None:
            id = str(uuid.uuid4())[:config.ACCOUNT_ID_LENGTH]

            self._table.put_item(
                Item={
                    'id': id,
                    'username': account.username,
                    'password': encrypted_password,
                    'host': account.host,
                    'cookie': encrypted_cookie,
                    'config': json.loads(account.config.json()) if account.config is not None else {}
                }
            )

            account.id = id
        else:
            self._table.update_item(
                Key={
                    'id': account.id
                },
                UpdateExpression='SET username = :username, password = :password, host = :host, cookie = :cookie, config = :config',
                ExpressionAttributeValues={
                    ':username': account.username,
                    ':password': encrypted_password,
                    ':host': account.host,
                    ':cookie': encrypted_cookie,
                    ':config': json.loads(account.config.json()) if account.config is not None else {}
                }
            )

        return account

    def _decrypt(self, account: model.Account) -> None:
        account.password = self._encrypter.decrypt(
            account.password
        )
        account.cookie = self._encrypter.decrypt(
            account.cookie # type: ignore[arg-type]
        )

    def _hydrate(self, item: dict[str, Any]) -> model.Account:
        account = model.Account.parse_obj(item)
        self._decrypt(account)

        return account

    def find_by_host_and_username(self, host: str, username: str) -> Optional[model.Account]:
        response = self._table.query(
            IndexName='HostAndUsernameIndex',
            KeyConditionExpression=(
                Key('host').eq(host)
            ),
            FilterExpression=(Attr('username').eq(username))
        )

        items = response['Items']
        if len(items) > 1:
            raise Exception(
                'Multiple records were returned for "host" and "username"'
            )

        return self._hydrate(response['Items'][0]) if len(items) == 1 else None

    def find(self, id: str) -> Optional[model.Account]:
        row = self._table.get_item(
            Key={
                'id': id
            }
        )

        return self._hydrate(row['Item']) if row is not None and 'Item' in row else None


def _validate_account_changeset(transient_account: model.Account, db_account: model.Account) -> bool:
    is_host_changed = db_account.host != transient_account.host
    is_username_changed = db_account.username != transient_account.username
    if is_host_changed or is_username_changed:
        raise RuntimeError('It is not allowed to change "username", "host" values for existing accounts.')

def authenticate2(transient_account: model.Account, tbl: AccountTable) -> model.Account:
    cookie = network.authenticate(transient_account)

    if transient_account.id is None:
        account = model.Account(
            username=transient_account.username,
            password=transient_account.password,
            host=transient_account.host
        )
    else:
        account = tbl.find(transient_account.id)

    _validate_account_changeset(transient_account, account)

    account.cookie = cookie
    account.config = transient_account.config
    account.password = transient_account.password

    return tbl.save(account)

def authenticate(acc_arg: model.Account, tbl: AccountTable) -> model.Account:
    cookie = network.authenticate(acc_arg)

    account = tbl.find(acc_arg.id) if acc_arg.id is not None else tbl.find_by_host_and_username(
        acc_arg.host,
        acc_arg.username
    )

    if account is None:
        account = model.Account(
            username=acc_arg.username,
            password=acc_arg.password,
            host=acc_arg.host
        )

    account.cookie = cookie
    account.config = acc_arg.config

    return tbl.save(account)
