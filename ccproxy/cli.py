import sys
from cryptography.fernet import Fernet 

if len (sys.argv) == 1:
    print("Command name wasn't provided, aborting ...")
    exit(1)

command = sys.argv[1]

if command == "generate-db-key":
    print(Fernet.generate_key().decode("utf-8"))