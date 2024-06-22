import uuid
from typing import Optional, Any
from ccproxy import config
from boto3.dynamodb.conditions import Key, Attr
from cryptography.fernet import Fernet
from mypy_boto3_dynamodb import DynamoDBServiceResource
from ccproxy import model, network


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

        if account.id is None:
            id = str(uuid.uuid4())[:config.ACCOUNT_ID_LENGTH]

            self._table.put_item(
                Item={
                    'id': id,
                    'username': account.username,
                    'password': encrypted_password,
                    'host': account.host,
                    'cookie': encrypted_cookie
                }
            )

            account.id = id
        else:
            self._table.update_item(
                Key={
                    'id': account.id
                },
                UpdateExpression='SET username = :username, password = :password, host = :host, cookie = :cookie',
                ExpressionAttributeValues={
                    ':username': account.username,
                    ':password': encrypted_password,
                    ':host': account.host,
                    ':cookie': encrypted_cookie
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


def authenticate(credentials: model.CredentialsEnvelope, account_table: AccountTable) -> model.Account:
    cookie = network.authenticate(credentials)

    account = account_table.find_by_host_and_username(
        credentials.host,
        credentials.username
    )
    if account is None:
        account = model.Account(
            username=credentials.username,
            password=credentials.password,
            host=credentials.host
        )

    account.cookie = cookie

    return account_table.save(account)
