import json
from ccproxy import container, model, network, main
from ccproxy.handlers import utils as handler_utils
import logging
from typing import Any

logger = logging.getLogger(__name__)

@handler_utils.exception_handler(logger)
def login_handler(event: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    account_table = container.create_account_table()

    account_to_auth = model.Account.parse_obj(handler_utils.extract_body(event))
    try:
        authenticated_account = main.authenticate(account_to_auth, account_table)
    except network.AuthContractError as e:
        logger.warning(
            f'Login error for user "{account_to_auth.username}": {str(e)}'
        )
        return {
            'statusCode': 403,
            'body': f'Failed to login "{account_to_auth.username}" - "{e.type.value}" error returned.'
        }

    return {
        'statusCode': 200,
        'body': json.loads(
            model.AccountResponse.from_account(authenticated_account).json()
        )
    }
