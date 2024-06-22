from ccproxy import api, config, model, main
from typing import Optional
import json
import boto3
from mypy_boto3_dynamodb import DynamoDBServiceResource, DynamoDBClient


def create_dynamodb_resource() -> DynamoDBServiceResource:
    return boto3.resource(
        'dynamodb',
        endpoint_url=_get_dynamodb_host()
    )


def create_dynamodb_client() -> DynamoDBClient:
    return boto3.client(
        'dynamodb',
        endpoint_url=_get_dynamodb_host()
    )


def _get_dynamodb_host() -> Optional[str]:
    config_host = config.DYNAMODB_HOST
    return None if config_host == '' else config_host


def create_account_table() -> main.AccountTable:
    dynamodb_resource = create_dynamodb_resource()

    return main.AccountTable(main.Encrypter(), dynamodb_resource)


def create_remote_device_controller(account: model.Account) -> api.RemoteDeviceController:
    with open(config.CONFIG_FILE) as reader:
        config_contents = json.loads(reader.read())

        return api.RemoteDeviceController(config_contents, account)
