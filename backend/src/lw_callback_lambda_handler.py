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
    BotInfo,
    NoticeList,
    NoticeContentPoint,
    NoticeContent,
    AccessToken,
    BotClientCredential,
    InstalledApp,
)
from .datastore.bot_api_cred import (
    BaseBotInfoRepository,
    BaseBotClientCredentialRepository,
    BaseInstalledAppRepository,
    BaseAccessTokenRepository,
    DynamoDBBotInfoRepository,
    DynamoDBBotClientCredentialRepository,
    DynamoDBInstalledAppRepository,
    DynamoDBAccessTokenRepository,
)
from .datastore.user_setting import (
    DynamoDBUserSettingRepository,
)
from .app.user_setting import (
    UserSettingApplication
)

from .lib import lineworks

logger = Logger()

app = LambdaFunctionUrlResolver()


GREETING_MESSAGE_TEXT = """熱中症への警戒度を配信します。
設定した都道府県等のいずれかの観測地点で、予測される暑さ指数が設定したレベルを超える場合に通知をします。

下のメニューの「配信設定」から設定してください。

【配信日時】
前日18時頃と当日7時頃の2回

【提供予定期間】
今期の配信は 2023年10月25日 で終了します。

【免責事項】
当サービスが提供する情報は、環境省が運営する「暑さ指数（WBGT）予測値等 電子情報提供サービス」が提供する予測値情報を利用しています。
予測値情報は急激な気象要因の変化などにより実際の値と差が生じる場合があります。その正確性について保証するものではありません。
また、当サービスは、システム障害またはサーバのメンテナンス等により予告なく一時的または長期に停止する場合がございます。それによってユーザーが被ったいかなる損害も当社は責任を負わないものとします。
熱中症予防に関する情報は、環境省の「熱中症予防情報サイト」をご覧ください。
https://www.wbgt.env.go.jp/sp/
"""

END_OF_SERVICE_MESSAGE_TEXT = """追加いただきありがとうございます。

今期の配信は 2023年10月25日 で終了しました。

次回の配信をお待ちください。
"""


def send_lw_text_message(text: str, domain_id: str,
                         user_id: str,
                         current_time: float,
                         bot_info: BotInfo,
                         access_token_repo: BaseAccessTokenRepository,
                         bot_client_cred_repo: BaseBotClientCredentialRepository,
                         install_app_repo: BaseInstalledAppRepository,
                         ):
    # create mssage content
    msg_content = {
        "content": {
            "type": "text",
            "text": text
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
        installed_app = install_app_repo.get_installed_app(domain_id)
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
    res = bot_api.send_message_to_user(msg_content,
                                       bot_info.bot_id,
                                       user_id)


@app.post("/bot-callback")
def post_bot_callback():
    logger.info(app.current_event.body)
    logger.info(app.current_event.headers)

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

    # send message
    try:
        send_lw_text_message(GREETING_MESSAGE_TEXT,
                             domain_id,
                             user_id,
                             current_time,
                             bot_info,
                             access_token_repo,
                             bot_client_cred_repo,
                             install_app_repo)
        return {}
    except Exception as e:
        logger.exception(e)
        raise


@app.post("/bot-callback-eos")
def post_bot_callback_eos():
    logger.info(app.current_event.body)
    logger.info(app.current_event.headers)

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

    # send message
    try:
        send_lw_text_message(END_OF_SERVICE_MESSAGE_TEXT,
                             domain_id,
                             user_id,
                             current_time,
                             bot_info,
                             access_token_repo,
                             bot_client_cred_repo,
                             install_app_repo)
        return {}
    except Exception as e:
        logger.exception(e)
        raise


@app.post("/install-update")
def eco_install_or_update_callback_handler():
    logger.info(app.current_event.body)
    logger.info(app.current_event.headers)

    headers = app.current_event.headers

    installed_app_table_name = os.environ.get("TABLE_INSTALLED_APPS")
    if installed_app_table_name is None:
        raise Exception("Please set TABLE_INSTALLED_APPS env")

    bot_id = os.environ.get("LW_BOT_ID")
    if bot_id is None:
        raise Exception("Please set LW_BOT_ID env")

    install_app_repo = DynamoDBInstalledAppRepository(installed_app_table_name)

    client_id = headers["client-id"]
    domain_id = headers["works-domain-id"]
    company_name = headers["works-company-name"]
    install_user = headers["works-install-user-id"]
    service_account = headers["works-install-service-account-id"]
    ver = headers["ver"]

    installed_app_obj = InstalledApp(
        domain_id=domain_id,
        service_account=service_account,
        ver=ver,
    )
    install_app_repo.put_installed_app(installed_app_obj)

    return {}


@app.post("/uninstall")
def eco_uninstall_callback_handler():
    logger.info(app.current_event.body)
    logger.info(app.current_event.headers)

    headers = app.current_event.headers

    installed_app_table_name = os.environ.get("TABLE_INSTALLED_APPS")
    if installed_app_table_name is None:
        raise Exception("Please set TABLE_INSTALLED_APPS env")

    access_token_table_name = os.environ.get("TABLE_ACCESS_TOKEN")
    if access_token_table_name is None:
        raise Exception("Please set TABLE_ACCESS_TOKEN env")

    user_setting_table_name = os.environ.get("TABLE_USER_SETTING")
    if user_setting_table_name is None:
        raise Exception("Please set TABLE_USER_SETTING env")

    bot_id = os.environ.get("LW_BOT_ID")
    if bot_id is None:
        raise Exception("Please set LW_BOT_ID env")

    install_app_repo = DynamoDBInstalledAppRepository(installed_app_table_name)
    access_token_repo = DynamoDBAccessTokenRepository(access_token_table_name)
    user_setting_repo = DynamoDBUserSettingRepository(user_setting_table_name)

    user_setting_app = UserSettingApplication(user_setting_repo)

    client_id = headers["client-id"]
    domain_id = headers["works-domain-id"]

    # delete innstall app
    install_app_repo.delete_installed_app(domain_id)

    # delete access token
    access_token_repo.delete_access_token_item(domain_id)

    # delete user settings
    user_setting_app.delete_user_settings_w_domain_id(domain_id)

    return {}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(event)
    return app.resolve(event, context)
