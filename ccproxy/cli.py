import sys
from cryptography.fernet import Fernet
import json
from os.path import isfile
import requests

def validate_config_file(config_file_path: str) -> None:
    if not isfile(config_file_path):
        raise RuntimeError(f'File "{config_file_path}" doesn\'t exist.')

    with open(config_file_path) as f:
        raw_config = json.loads(f.read())

    from ccproxy import model
    model.Config(**raw_config)

def create_account(login_url: str, cc_host, username: str, password: str, config_file_path: str) -> str:
    validate_config_file(config_file_path)

    with open(config_file_path) as f:
        config = json.loads(f.read())

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }
    payload = {
        'host': cc_host,
        'username': username,
        'password': password,
        'config': config
    }

    response = requests.request(
        'POST', login_url, json=payload, headers=headers
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

            case 'validate-config':
                if (len(sys.argv) != 3):
                    print('Name of the config file must be provided, e.g. : python ccproxy/cli.py validate-config config.json')
                    exit(1)

                validate_config_file(sys.argv[2])
                print("All good 👌, given config is valid.")

            case 'create-account':
                if (len(sys.argv) != 7):
                    print('Required parameters were not provided. Valid usage example: python ccproxy/cli.py create-account https://login.example.org https://example.org jdoe 1234 config.json')
                    exit(1)

                id = create_account(
                    sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
                )
                print(id)
    except Exception as e:
        print(e)
        exit(1)
