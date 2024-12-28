import sys
from typing import Any, Optional
from cryptography.fernet import Fernet
from ccproxy import model
import json
from os.path import isfile
import requests


def _do_post_request_with_json(url: str, payload: dict[str, Any]) -> requests.Response:
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }

    return requests.request('POST', url, json=payload, headers=headers)

def _read_json_file(file_path: str) -> dict[str, Any]:
    if not isfile(file_path):
        raise RuntimeError(f'File "{file_path}" doesn\'t exist.')

    with open(file_path) as file:
        return json.load(file) # type: ignore[no-any-return]

def create_account_on_server(
    ccproxy_login_url: str,
    account: model.Account
) -> model.AccountResponse:
    response = _do_post_request_with_json(
        ccproxy_login_url,
        json.loads(account.json()) # TODO use Pydantic 2.x's API
    )

    if response.status_code != 200:
        raise RuntimeError(f'Unable to create account, returned error: {str(response.text)}')

    return model.AccountResponse.parse_raw(response.text)

def update_account_on_server(
    ccproxy_update_account_url: str,
    payload: model.AccountUpdatePayload
) -> model.AccountResponse:
    response = _do_post_request_with_json(
        ccproxy_update_account_url,
        json.loads(payload.json()) # TODO use Pydantic 2.x's API
    )

    if response.status_code != 200:
        raise RuntimeError(f'Unable to update account, returned error: {str(response.text)}')

    return model.AccountResponse.parse_raw(response.text)

def create_account_on_server_from_file(
    ccproxy_login_url: str,
    config_file_path: str,
    password: Optional[str],
) -> model.AccountResponse:
    account_dict = _read_json_file(config_file_path)

    # even though it's not recommended, password field can be a part of a config file. 
    # In this case it's not necessary to provide it as an arg
    if password is not None:
        account_dict = account_dict | { 'password': password }

    account = model.Account.parse_obj(account_dict) # validation
    
    return create_account_on_server(ccproxy_login_url, account)

def update_account_on_server_from_file(
    ccproxy_update_account_url: str,
    account_id: str,
    config_file_path: str,
) -> model.AccountResponse:
    payload_dict = _read_json_file(config_file_path) | { 'id': account_id }

    return update_account_on_server(
        ccproxy_update_account_url,
        model.AccountUpdatePayload.parse_obj(payload_dict)
    )

if __name__ == '__main__':
    if len (sys.argv) == 1:
        print("Command name wasn't provided, aborting ...")
        exit(1)

    try:
        match sys.argv[1]:
            case 'generate-db-key':
                print(Fernet.generate_key().decode('utf-8'))

            case 'create-account':
                if (len(sys.argv) != 5):
                    print('Required parameters were not provided. Valid usage example: python ccproxy/cli.py create-account https://ccproxy-login.example.com account.json password1234')
                    exit(1)

                response = create_account_on_server_from_file(
                    sys.argv[2], sys.argv[3], sys.argv[4]
                )
                print(response.id)

            case 'update-account':
                if (len(sys.argv) != 5):
                    print('Required parameters were not provided. Valid usage example: python ccproxy/cli.py update-account https://update-account.example.com account-id account.json')
                    exit(1)

                response = update_account_on_server_from_file(
                    sys.argv[2], sys.argv[3], sys.argv[4]
                )
                print(response.id)
    except Exception as e:
        print(e)
        exit(1)
