import sys
from typing import Optional
from cryptography.fernet import Fernet
from ccproxy import model
import json
from os.path import isfile
import requests

def create_account_on_server(ccproxy_login_url: str, account: model.Account) -> str:
    payload = json.loads(account.json()) # TODO use Pydantic 2.x's API

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }

    response = requests.request(
        'POST', ccproxy_login_url, json=payload, headers=headers
    )

    if response.status_code != 200:
        raise RuntimeError(f'Unable to create account, returned error: {str(response.text)}')

    return response.text # should contain 'id' of a created account

def create_account_from_file(
    ccproxy_login_url: str,
    config_file_path: str,
    password: Optional[str],
) -> str:
    with open(config_file_path) as f:
        create_account_raw = json.loads(f.read())

    account_dict = create_account_raw 
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

                id = create_account_from_file(
                    sys.argv[2], sys.argv[3], sys.argv[4]
                )
                print(id)
    except Exception as e:
        print(e)
        exit(1)
