from ccproxy import config, container


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
