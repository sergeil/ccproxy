import sys
from cryptography.fernet import Fernet
import json
from os.path import isfile

if len (sys.argv) == 1:
    print("Command name wasn't provided, aborting ...")
    exit(1)

match sys.argv[1]:
    case 'generate-db-key':
        print(Fernet.generate_key().decode('utf-8'))

    case 'validate-config':
        if (len(sys.argv) != 3):
            print('Name of the config file must be provided, e.g. : python ccproxy/cli.py config.json')
            exit(1)

        config_file_path = sys.argv[2]
        if not isfile(config_file_path):
            print(f'File "{config_file_path}" doesn\'t exist.')
            exit(1)

        with open(config_file_path) as f:
            raw_config = json.loads(f.read())

        from ccproxy import model
        from pydantic import ValidationError
        try:
            model.Config(**raw_config)
        except ValidationError as e:
            print(e)
            exit(1)
        else:
            print("All good 👌, given config is valid.")