import os
import urllib.parse
import json

from datetime import datetime, timedelta

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver, Response, content_types, CORSConfig
from aws_lambda_powertools.event_handler.exceptions import (
    NotFoundError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from .models import (
    NoticeList,
    NoticeContentPoint,
    NoticeContent,
    AccessToken,
    BotClientCredential,
)
from .datastore.bot_api_cred import (
    DynamoDBBotInfoRepository,
    DynamoDBBotClientCredentialRepository,
    DynamoDBInstalledAppRepository,
    DynamoDBAccessTokenRepository,
)
from .lib import lineworks

logger = Logger()

cors_config = CORSConfig()
app = LambdaFunctionUrlResolver()


GREETING_MESSAGE_TEXT = """熱中症への警戒度を配信します。
設定した都道府県等のいずれかの観測地点で、予測される暑さ指数が設定したレベルを超える場合に通知をします。

下のメニューの「配信設定」から設定してください。

配信日時: 前日18時頃と当日7時頃の2回

【免責事項】
当サービスが提供する情報は、環境省が運営する「暑さ指数（WBGT）予測値等電子情報提供サービス」が提供する予測値情報を利用しています。
予測値情報は急激な気象要因の変化などにより実際の値と差が生じる場合があります。その正確性について保証するものではありません。
熱中症予防に関する情報は、環境省の「熱中症予防情報サイト」をご覧ください。
https://www.wbgt.env.go.jp/sp/
"""


@app.post("/bot-callback")
def post_bot_callback():
    logger.info(app.current_event.headers)
    logger.info(app.current_event.body)
    logger.info(app.current_event.decoded_body)
    logger.info(app.current_event.query_string_parameters)

    body: dict = app.current_event.json_body
    body_raw = app.current_event.body
    headers = app.current_event.headers

    header_botid = headers["x-works-botid"]
    header_sig = headers["x-works-signature"]

    current_time = datetime.now().timestamp()

    access_token_table_name = os.environ.get("TABLE_ACCESS_TOKEN")
    if access_token_table_name is None:
        raise Exception("Please set TABLE_ACCESS_TOKEN env")

    bot_info_table_name = os.environ.get("TABLE_BOT_INFO")
    if bot_info_table_name is None:
        raise Exception("Please set TABLE_BOT_INFO env")

    bot_client_cred_table_name = os.environ.get("TABLE_BOT_CLIENT_CRED")
    if bot_client_cred_table_name is None:
        raise Exception("Please set TABLE_BOT_CLIENT_CRED env")

    installed_app_table_name = os.environ.get("TABLE_INSTALLED_APPS")
    if installed_app_table_name is None:
        raise Exception("Please set TABLE_INSTALLED_APPS env")

    bot_id = os.environ.get("LW_BOT_ID")
    if bot_id is None:
        raise Exception("Please set LW_BOT_ID env")

    bot_info_repo = DynamoDBBotInfoRepository(bot_info_table_name)
    bot_client_cred_repo = DynamoDBBotClientCredentialRepository(bot_client_cred_table_name)
    install_app_repo = DynamoDBInstalledAppRepository(installed_app_table_name)
    access_token_repo = DynamoDBAccessTokenRepository(access_token_table_name)

    # Check bot id
    if header_botid != bot_id:
        raise Exception("Bot id is invalid.")

    # Get bot info
    bot_info = bot_info_repo.get_bot_info(bot_id)
    if bot_info is None:
        raise Exception("Please set Bot Info.")

    # Verify request
    if bot_info.bot_secret is not None and not lineworks.bot.validate_request(body_raw.encode(), header_sig, bot_info.bot_secret):
        # invalid request
        logger.warn("Invalid request")
        return

    domain_id = str(body["source"]["domainId"])
    user_id = body["source"]["userId"]

    # create mssage content
    msg_content = {
        "content": {
            "type": "text",
            "text": GREETING_MESSAGE_TEXT
        }
    }

    # Get access token
    access_token_obj = access_token_repo.get_access_token_item(domain_id)
    # Check existence and expiration
    if access_token_obj is None or access_token_obj.expired_at < current_time:
        # Renew access token
        client_cred = bot_client_cred_repo.get_bot_client_credential(bot_info.bot_id, bot_info.provider_domain_id)
        if client_cred is None:
            logger.warn("A client credential is not set. Please set values")
            return

        # Eco app
        installed_app = install_app_repo.get_installed_app(client_cred.client_id, domain_id)
        if installed_app is None:
            raise Exception("Installed App does not exist.")
        service_account = installed_app.service_account

        res = lineworks.auth.get_access_token(client_cred.client_id,
                                              client_cred.client_secret,
                                              service_account,
                                              client_cred.private_key,
                                              "bot")
        access_token_obj = AccessToken(
            bot_id=bot_info.bot_id,
            domain_id=domain_id,
            access_token=res["access_token"],
            created_at=current_time,
            expired_at=current_time + int(res["expires_in"])
        )
        # Put access token
        access_token_repo.put_access_token_item(access_token_obj)

    bot_api = lineworks.bot.BotApi(access_token_obj.access_token)

    # send message
    try:
        res = bot_api.send_message_to_user(msg_content,
                                           bot_info.bot_id,
                                           user_id)
        return
    except Exception as e:
        logger.exception(e)
        raise

# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(event)
    return app.resolve(event, context)
