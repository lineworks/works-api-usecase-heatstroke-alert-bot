import json

import jwt
from datetime import datetime
import urllib
import requests


BASE_AUTH_URL = 'https://auth.worksmobile.com/oauth2/v2.0'


class AuthRequestError(Exception):
    """Auth リクエストエラー
    """


def __get_jwt(client_id: str, service_account: str, privatekey: str) -> str:
    """Generate JWT for access token

    :param client_id: Client ID
    :param service_account: Service Account
    :param privatekey: Private Key
    :return: JWT
    """
    current_time = datetime.now().timestamp()
    iss = client_id
    sub = service_account
    iat = current_time
    exp = current_time + (60 * 60) # 1 hour

    jws = jwt.encode(
        {
            "iss": iss,
            "sub": sub,
            "iat": iat,
            "exp": exp
        }, privatekey, algorithm="RS256")

    return jws


def get_access_token(client_id: str, client_secret: str, service_account: str, privatekey: str, scope: str) -> dict:
    """Get Access Token

    :param client_id: Client ID
    :param client_secret: Client ID
    :param service_account: Service Account
    :param privatekey: Private Key
    :param scope: OAuth Scope
    :return: response
    """
    # Get JWT
    jwt = __get_jwt(client_id, service_account, privatekey)

    # Get Access Token
    url = '{}/token'.format(BASE_AUTH_URL)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    params = {
        "assertion": jwt,
        "grant_type": urllib.parse.quote("urn:ietf:params:oauth:grant-type:jwt-bearer"),
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }

    form_data = params

    r = requests.post(url=url, data=form_data, headers=headers)

    try:
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise AuthRequestError(e)

    return r.json()



def refresh_access_token(client_id, client_secret, refresh_token):
    """アクセストークン更新
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    params = {
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    form_data = params

    r = requests.post(url=ACCESS_TOKEN_URI, data=form_data, headers=headers)

    try:
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise AuthRequestError(e)


    body = json.loads(r.text)

    return body

