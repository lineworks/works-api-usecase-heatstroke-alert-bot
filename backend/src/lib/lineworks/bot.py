import json

import hashlib
import hmac
from base64 import b64encode, b64decode

import requests

from . import base


BASE_API_URL = "https://www.worksapis.com/v1.0"


def validate_request(body: bytes, signature: str, bot_secret: str) -> bool:
    """Validate request

    :param body: request body
    :param signature: value of X-WORKS-Signature header
    :param bot_secret: Bot Secret
    :return: is valid
    """
    secretKey = bot_secret.encode()
    payload = body

    # Encode by HMAC-SHA256 algorithm
    encoded_body = hmac.new(secretKey, payload, hashlib.sha256).digest()
    # BASE64 encode
    encoded_b64_body = b64encode(encoded_body).decode()

    # Compare
    return encoded_b64_body == signature


class BotApi(base.BaseApi):
    def send_message_to_user(self, content: dict, bot_id: str, user_id: str):
        """メッセージ送信"""
        path = "/bots/{}/users/{}/messages".format(bot_id, user_id)

        return self.post(path, content)


    def send_message_to_channel(self, content: dict, bot_id: str, channel_id: str):
        """メッセージ送信"""
        path = "/bots/{}/channels/{}/messages".format(bot_id, channel_id)

        return self.post(path, content)


    def get_attachments(self, bot_id, file_id, access_token):
        """コンテンツダウンロード"""
        url = "{}/bots/{}/attachments/{}".format(BASE_API_URL, bot_id, file_id)

        headers = {
              'Authorization' : "Bearer {}".format(access_token)
            }

        r = requests.get(url=url, headers=headers)

        try:
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise base.BotApiRequestError(e)

        return r.content


    def post_attachments(self, file_name, bot_id, access_token):
        url = "{}/bots/{}/attachments".format(BASE_API_URL, bot_id)

        headers = {
              'Content-Type' : 'application/json',
              'Authorization' : "Bearer {}".format(access_token)
            }

        params = {
            "fileName": file_name
        }
        form_data = json.dumps(params)

        r = requests.post(url=url, data=form_data, headers=headers)

        try:
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise base.BotApiRequestError(e)

        return r.json()


def upload_file(url, file_data, access_token):
    headers = {
        'Authorization' : "Bearer {}".format(access_token),
    }

    file = {
        'FileData': file_data,
    }

    r = requests.post(url=url, files=file, headers=headers, timeout=180)

    try:
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise BotApiRequestError(e)

    return r.json()
