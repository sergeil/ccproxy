from ccproxy import config, container, model
from typing import Any


def create_accounts_table_if_not_exists() -> bool:
    client = container.create_dynamodb_client()

    table_name = config.ACCOUNTS_TABLE

    if table_name not in client.list_tables()['TableNames']:
        client.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'id',
                    'KeyType': 'HASH',
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'id',
                    'AttributeType': 'S',
                },
                {
                    'AttributeName': 'host',
                    'AttributeType': 'S',
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'HostAndUsernameIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'host',
                            'KeyType': 'HASH',
                        }
                    ],
                    "Projection": {
                        "ProjectionType": "ALL"
                    },
                }
            ]
        )

        return True

    return False

def create_account_object(
    override: dict[str, Any] = {},
    config_override: dict[str, Any] = {},
    device_override: dict[str, Any] = {}
) -> model.Account:
    merged_obj: dict[str, Any] = {
        'username': 'foo-username',
        'password': 'foo-password',
        'host': 'https://example.org',
        'cookie': 'foo-cookie',
        'config': create_account_config_object(config_override),
        'device': create_account_device_object(device_override)
    } | override

    return model.Account(**merged_obj)

def create_account_config_object(override: dict[str, Any] = {}) -> model.Config:
    merged_obj: dict[str, Any] = {
        'messages': {
            'bla_action': ['foo', 'bar']
        },
        'actions': {
            'bla_action': 'bla_action_path'
        }
    } | override

    return model.Config(**merged_obj)

def create_account_device_object(override: dict[str, Any] = {}) -> model.Device:
    merged_obj = {
        'device_name': 'foo-dn',
        'platform': 'foo-plt',
        'push_token': 'foo-pt'
    } | override

    return model.Device(**merged_obj)
