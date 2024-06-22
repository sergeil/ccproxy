from enum import Enum
from typing import Any
import requests
from requests import Response
from ccproxy import model, config


class AuthContractError(RuntimeError):
    class Types(Enum):
        NO_STATUS_FIELD = 'no_status_field'
        NOT_OK_STATUS = 'not_ok_status'
        NO_COOKIE_HEADER = 'no_cookie_header'
        INVALID_SET_COOKIE_HEADER = 'invalid_set_cookie_header'

    def __init__(self, *args: object, type: Types) -> None:
        super().__init__(*args)
        self.type = type


def do_request(url: str, method: str, json: dict[Any, Any] = {}, headers: dict[str, Any] = {}) -> Response:
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
    } | headers

    response = requests.request(
        method, url, json=json, headers=headers, verify=False
    )

    return response


def do_authenticated_request(account: model.Account, url: str, method: str, json: dict[str, Any] = {}, headers: dict[str, Any] = {}) -> Response:
    headers = {
        'Cookie': f"CurrentPath=; {account.cookie}"
    } | headers

    return do_request(url, method, json, headers)


def authenticate(credentials: model.CredentialsEnvelope) -> str:
    payload = {
        'UserName': credentials.username,
        'Password': credentials.password,
        'DeviceName': config.DEVICE_NAME,
        'OS': 'iOS',
        'PushToken': config.PUSH_TOKEN,
        'RememberMe': False
    }

    response = do_request(f'{credentials.host}/Login', 'POST', payload)
    _validate_auth_reponse(response)

    raw_cookie = response.headers['Set-Cookie'].split(';')
    if len(raw_cookie) != 2:
        raise AuthContractError(
            'Wrongly formatted "Set-Cookie" header returned.',
            type=AuthContractError.Types.INVALID_SET_COOKIE_HEADER
        )
    return raw_cookie[0]


def _validate_auth_reponse(response: Response) -> None:
    body = response.json()
    headers = response.headers

    if 'Status' not in body:
        raise AuthContractError(
            'Server returned invalid response, "Status" field is missing.',
            type=AuthContractError.Types.NO_STATUS_FIELD
        )
    elif body['Status'] != 'OK':
        raise AuthContractError(
            f"Expected OK response, but server returned \"{body['Status'][0:32]}\".",
            type=AuthContractError.Types.NOT_OK_STATUS
        )
    elif 'Set-Cookie' not in headers:
        raise AuthContractError(
            'Cookie was not server by the server.',
            type=AuthContractError.Types.NO_COOKIE_HEADER
        )
