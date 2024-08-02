from ccproxy import container, model, network, main
from ccproxy.handlers import utils as handler_utils
import logging
from typing import Any

logger = logging.getLogger(__name__)

@handler_utils.exception_handler(logger)
def login_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    account_table = container.create_account_table()

    # TODO consider using AccountCreatePayload
    credentials = model.Account.parse_obj(handler_utils.extract_body(event))
    try:
        authenticated_account = main.authenticate(credentials, account_table)
    except network.AuthContractError as e:
        logger.warning(
            f'Login error for user "{credentials.username}": {str(e)}'
        )
        return {
            'statusCode': 403,
            'body': f'Failed to login "{credentials.username}" - "{e.type.value}" error returned.'
        }

    return {
        'statusCode': 200,
        # TODO consider returning the whole Account (make sure though
        # that we intentionally select which fields to return, not everything)
        'body': authenticated_account.id
    }
