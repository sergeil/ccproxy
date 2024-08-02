from ccproxy import container, model
from ccproxy.handlers import utils as handler_utils
import logging
import json
from typing import Any

logger = logging.getLogger(__name__)

@handler_utils.exception_handler(logger)
def update_account(event: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    account_table = container.create_account_table()

    payload = model.AccountUpdatePayload.parse_obj(handler_utils.extract_body(event))
    
    account = account_table.find(payload.id)
    if account is None:
        raise handler_utils.LambdaHttpError(f'Unable to find account with id #{payload.id}')
    
    account.config = payload.config
    account.device = payload.device
    account = account_table.save(account)

    result = model.AccountUpdatePayload(
        id=account.id,
        config=account.config,
        device=account.device
    )

    return {
        'statusCode': 200,
        # TODO return only fields we want, we can use Pydantic 2.x's "model_dump"
        # & include parameter for this
        'body': json.loads(result.json())
    }