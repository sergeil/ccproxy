import json
from ccproxy import container, model, network, main
from ccproxy.handlers import utils as handler_utils
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


@handler_utils.exception_handler(logger)
def login_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    validation_result = _validate_request(event)
    if validation_result is not None:
        return validation_result

    try:
        body = json.loads(event['body'])
    except Exception:
        return {
            'statusCode': 400,
            'message': 'Body of the request should contain JSON object.',
            '_errorType': 'invalid_json_given',
        }

    if not isinstance(body, dict):
        return {
            'statusCode': 400,
            'message': 'Body of the request should contain JSON object.',
            '_errorType': 'not_object_body_payload',
        }

    account_table = container.create_account_table()

    credentials = model.CredentialsEnvelope.parse_obj(body)
    try:
        account = main.authenticate(credentials, account_table)
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
        'body': account.id
    }


def _validate_request(event: dict[str, Any]) -> Optional[dict[str, Any]]:
    if 'body' not in event:
        return {
            'statusCode': 400,
            'message': 'This function is meant to be used only with "POST" method.',
            '_errorType': 'no_body_param'
        }

    return None
