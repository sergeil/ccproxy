import sys
from typing import Optional, TypeAlias
from cryptography.fernet import Fernet
import pydantic
from ccproxy import model
import json
from os.path import isfile
import requests

AccountId: TypeAlias = str

def _do_post_request_with_json(url: str, payload: dict) -> requests.Response:
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }

    return requests.request('POST', url, json=payload, headers=headers)

def create_account_on_server(ccproxy_login_url: str, account: pydantic.BaseModel) -> AccountId:
    response = _do_post_request_with_json(
        ccproxy_login_url,
        json.loads(account.json()) # TODO use Pydantic 2.x's API
    )

    if response.status_code != 200:
        raise RuntimeError(f'Unable to create account, returned error: {str(response.text)}')

    return response.text # should contain 'id' of a created account

def update_account_on_server_from_file(
    ccproxy_update_account_url: str,
    payload: model.AccountUpdatePayload
) -> str:
    pass

def create_account_on_server_from_file(
    ccproxy_login_url: str,
    config_file_path: str,
    password: Optional[str],
) -> AccountId:
    if not isfile(config_file_path):
        raise RuntimeError(f'File "{config_file_path}" doesn\'t exist.')

    with open(config_file_path) as f:
        account_dict = json.loads(f.read())

    if password is not None:
        account_dict = account_dict | { 'password': password }

    account = model.Account.parse_obj(account_dict) # validation
    
    return create_account_on_server(ccproxy_login_url, account)

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

                id = create_account_on_server_from_file(
                    sys.argv[2], sys.argv[3], sys.argv[4]
                )
                print(id)

            case 'update-account':
                if (len(sys.argv) != 5):
                    print('Required parameters were not provided. Valid usage example: python ccproxy/cli.py update-account https://update-account.example.com account-id account.json')
                    exit(1)

                id = update_account_on_server_from_file(
                    sys.argv[2], sys.argv[3], sys.argv[4]
                )
                print(id)
    except Exception as e:
        print(e)
        exit(1)
