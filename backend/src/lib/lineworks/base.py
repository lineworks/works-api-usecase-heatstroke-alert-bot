import json
import time
import requests


BASE_API_URL = "https://www.worksapis.com/v1.0"
RETRY_COUNT_MAX = 5


class BotApiBaseError(requests.RequestException):
    """Bot API Base Error"""


class BotApiRequestRetryOver(BotApiBaseError):
    """Bot API リクエスト Retry over
    """


class BotApiRequestError(BotApiBaseError):
    """Bot API リクエストエラー
    """


class BaseApi():
    def __init__(self, access_token: str, request_try_count=RETRY_COUNT_MAX):
        self.access_token = access_token
        self.request_try_count = request_try_count

        self.headers = {
          'Content-Type' : 'application/json',
          'Authorization' : "Bearer {}".format(access_token)
        }

    def __http(self, func, **kwargs) -> dict:
        res = None
        for i in range(self.request_try_count):
            try:
                # Reply message
                r = func(headers=self.headers, allow_redirects=False, **kwargs)
                res = r
                r.raise_for_status()
                if r.text is not None and r.text != "":
                    return r.json()
                return r.text
            except requests.RequestException as e:
                body = e.response.json()
                status_code = e.response.status_code
                if status_code == 429:
                    # Requests over rate limit.
                    pass
                else:
                    raise BotApiRequestError(response=e.response)

                # wait and retry
                time.sleep(2 ** i)
            else:
                break
        if res is not None:
            raise BotApiRequestRetryOver(response=res)

    def get(self, path: str, params: dict) -> dict:
        url = "{}{}".format(BASE_API_URL, path)

        res = self.__http(requests.get, url=url, params=params)
        return res

    def post(self, path: str, data: dict) -> dict:
        url = "{}{}".format(BASE_API_URL, path)

        form_data = json.dumps(data)

        res = self.__http(requests.post, url=url, data=form_data)
        return res
