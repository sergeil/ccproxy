from decouple import config

ACCOUNT_ID_LENGTH = 8

DB_ENCRYPTION_KEY = config('DB_ENCRYPTION_KEY')
ACCOUNTS_TABLE = config('ACCOUNTS_TABLE')
CONFIG_FILE = config('CONFIG_FILE')
DYNAMODB_HOST = config('DYNAMODB_HOST')

# Used for integration testing
IT_USERNAME = config('INTEST_USERNAME')
IT_PASSWORD = config('INTEST_PASSWORD')
IT_HOST = config('INTEST_HOST')
