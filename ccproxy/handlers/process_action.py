from requests import HTTPError
from ccproxy import container, config, api, model, main
from typing import Any, Optional
import logging
from ccproxy.handlers import utils as handler_utils

logger = logging.getLogger(__name__)

_ACCOUNT_HEADER_NAME = 'x-ccproxy-account'


@handler_utils.exception_handler(logger)
def process_action_handler(event: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if 'lambda_tender' in event:
        return {
            'statusCode': 418,
            'body': 'Brewing lambda'
        }

    q = event['queryStringParameters']

    validation_result = _validate_request(event)
    if validation_result is not None:
        return validation_result

    account_table = container.create_account_table()

    action = q['action']

    account_id_val = event['headers'][_ACCOUNT_HEADER_NAME][0:config.ACCOUNT_ID_LENGTH]
    account = account_table.find(account_id_val)
    if account is None:
        return {
            'statusCode': 400,
            'body': f'Unable to find account "{account_id_val}".'
        }

    try:
        message = do_api_call(account, account_table, action)
    except api.RemoteDeviceController.UnknownActionError:
        return {
            'statusCode': 400,
            'body': f'Unkown action "{action[0:16]}" given.',
            '_errorType': 'unknown_action'
        }

    return {
        'statusCode': 200,
        'body': message
    }


def _validate_request(event: dict[str, Any]) -> Optional[dict[str, Any]]:
    if 'action' not in event['queryStringParameters']:
        return {
            'statusCode': 400,
            'body': '"action" is not specified. For example, you can append this to URL: ?action=open_garage',
            '_errorType': 'action_not_specified'
        }

    if _ACCOUNT_HEADER_NAME not in event['headers']:
        return {
            'statusCode': 400,
            'body': f'Account not specified, use "{_ACCOUNT_HEADER_NAME}" header for that.',
            '_errorType': 'account_not_specified'
        }

    return None


# TODO convert to _do_api_call
def do_api_call(account: model.Account, account_table: main.AccountTable, action: str, is_retry: bool = False) -> str:
    device_controller = container.create_remote_device_controller(account)

    try:
        return device_controller.toggle(action)
    except HTTPError as e:
        if e.response.status_code == 401 and not is_retry:
            logger.info(
                f'Auth token expired, re-authenticating user "{account.username}"'
            )
            refreshed_account = main.authenticate(account, account_table)

            return do_api_call(refreshed_account, account_table, action, True)
        else:
            raise e
