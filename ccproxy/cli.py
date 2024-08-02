import sys
from cryptography.fernet import Fernet
from ccproxy import model
import json
from os.path import isfile
import requests

def validate_account_config_file(config_file_path: str) -> None:
    if not isfile(config_file_path):
        raise RuntimeError(f'File "{config_file_path}" doesn\'t exist.')

    with open(config_file_path) as f:
        raw_config = json.loads(f.read())

    model.AccountCreatePayload(**raw_config)

def create_account(
    ccproxy_login_url: str,
    config_file_path: str,
    password: str,
) -> str:
    # validate_account_config_file(config_file_path)

    with open(config_file_path) as f:
        create_account_raw = json.loads(f.read())

    create_account_dict = create_account_raw | { 'password': password }

    account_create_payload = model.AccountCreatePayload.parse_obj(create_account_dict) # validation
    payload = json.loads(account_create_payload.json()) # TODO use Pydantic 2.x's API

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }

    response = requests.request(
        'POST', ccproxy_login_url, json=payload, headers=headers
    )

    if response.status_code != 200:
        raise RuntimeError(f'Unable to create account, returned error: {str(response.text)}')

    return response.text # should contain 'id' of a created account


if __name__ == '__main__':
    if len (sys.argv) == 1:
        print("Command name wasn't provided, aborting ...")
        exit(1)

    try:
        match sys.argv[1]:
            case 'generate-db-key':
                print(Fernet.generate_key().decode('utf-8'))

            case 'validate-account-config':
                if (len(sys.argv) != 3):
                    print('Name of the config file must be provided, e.g. : python ccproxy/cli.py validate-account-config config.json')
                    exit(1)

                validate_account_config_file(sys.argv[2])
                print("All good 👌, given config is valid.")

            case 'create-account':
                if (len(sys.argv) != 5):
                    print('Required parameters were not provided. Valid usage example: python ccproxy/cli.py create-account https://ccproxy-login.example.com account.json password1234')
                    exit(1)

                id = create_account(
                    sys.argv[2], sys.argv[3], sys.argv[4]
                )
                print(id)
    except Exception as e:
        print(e)
        exit(1)
