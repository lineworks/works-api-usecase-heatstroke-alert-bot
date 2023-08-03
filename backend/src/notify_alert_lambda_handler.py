import os
import json
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta, time

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import event_source, SQSEvent


from .datastore.wbgt import (
    DynamoDBWBGTRepository,
    InMemoryWBGTPointRepository,
    InMemoryWBGTPrefPointRepository,
    InMemoryWBGTAlertLevelRepository,
)
from .datastore.bot_api_cred import (
    DynamoDBBotInfoRepository,
    DynamoDBBotClientCredentialRepository,
    DynamoDBInstalledAppRepository,
    DynamoDBAccessTokenRepository,
)

from .service.wbgt import (
    WBGTService
)
from .app.wbgt_prediction import (
    WBGTPredictionApplication,
)
from .service.publisher import SQSMessagePublisher
from .models import (
    NoticeList,
    NoticeContentPoint,
    NoticeContent,
    AccessToken,
    BotClientCredential,
)
from .lib import lineworks

logger = Logger()


NOTIFY_TEXT_GUIDE = """
【暑さ指数 (WBGT) の目安】
31以上: 危険
28以上31未満: 厳重警戒
25以上28未満: 警戒
25未満: 注意

※ 配信の停止は「配信設定」から行います。
"""

NOTIFY_TEXT_POINT_INFO_FMT = """
予想される {} の観測地点別の日最高暑さ指数 (WBGT) は以下の通りです。

{}
"""

def notify(notice_content_raw: str):
    logger.info(notice_content_raw)
    current_time = datetime.now().timestamp()
    logger.info(current_time)

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

    notice_content = NoticeContent.parse_raw(notice_content_raw)
    logger.info(notice_content)
    logger.info("UserID: {}".format(notice_content.user_setting.user_id))

    # Get bot info
    bot_info = bot_info_repo.get_bot_info(bot_id)
    if bot_info is None:
        raise Exception("Please set Bot Info.")

    # create mssage content
    msg_contents = [
        {
            "content": {
                "type": "flex",
                "altText": "{} の予測です。".format(notice_content.prefecture.pref_name_ja),
                "contents": {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "text": "{}".format(notice_content.day.strftime("%m/%d")),
                                "type": "text",
                                "size": "lg"
                            },
                            {
                                "layout": "vertical",
                                "type": "box",
                                "contents": [
                                    {
                                        "text": "{}".format(notice_content.alert_level.alert_level_subtitle_ja),
                                        "type": "text",
                                        "size": "lg",
                                        "style": "normal",
                                        "align": "center",
                                    }
                                ]
                            },
                            {
                                "layout": "vertical",
                                "type": "box",
                                "contents": [
                                    {
                                        "text": "{}".format(notice_content.alert_level.alert_level_title_ja),
                                        "type": "text",
                                        "style": "normal",
                                        "align": "center",
                                        "wrap": True,
                                        "size": "xl",
                                        "gravity": "center",
                                        "color": "{}".format(notice_content.alert_level.alert_level_text_color)
                                    }
                                ],
                                "backgroundColor": "{}".format(notice_content.alert_level.alert_level_background_color),
                                "spacing": "none",
                                "margin": "md",
                                "borderWidth": "none",
                                "cornerRadius": "none"
                            },
                            {
                                "layout": "vertical",
                                "type": "box",
                                "contents": [
                                    {
                                        "text": "の予測です",
                                        "type": "text",
                                        "size": "md",
                                        "style": "normal",
                                        "align": "end",
                                    }
                                ],
                                "spacing": "none",
                                "margin": "md"
                            },
                            {
                                "layout": "vertical",
                                "type": "box",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "{}".format(notice_content.alert_level.alert_level_description_ja),
                                        "wrap": True,
                                        "decoration": "none"
                                    }
                                ],
                                "borderWidth": "none",
                                "margin": "sm"
                            },
                            {
                                "layout": "vertical",
                                "type": "box",
                                "contents": [
                                    {
                                        "text": NOTIFY_TEXT_POINT_INFO_FMT.format(
                                            notice_content.prefecture.pref_name_ja,
                                            ', '.join([ "{}{}".format(content_point.point.point_name_ja, content_point.max_wbgt.value) for content_point in notice_content.points])
                                        ),
                                        "wrap": True,
                                        "type": "text"
                                    },
                                    {
                                        "text": NOTIFY_TEXT_GUIDE,
                                        "wrap": True,
                                        "type": "text"
                                    }
                                ],
                                "borderWidth": "none",
                                "margin": "lg"
                            },
                            {
                                "action": {
                                    "type": "uri",
                                    "label": "熱中症予防対策を確認",
                                    "uri": "https://www.wbgt.env.go.jp/sp/heatillness.php"
                                },
                                "type": "button",
                                "style": "link"
                            }
                        ]
                    }
                }
            }
        }
    ]
    logger.info(msg_contents)

    # Get access token
    access_token_obj = access_token_repo.get_access_token_item(notice_content.user_setting.domain_id)
    # Check existence and expiration
    if access_token_obj is None or access_token_obj.expired_at < current_time:
        # Renew access token
        client_cred = bot_client_cred_repo.get_bot_client_credential(bot_info.bot_id, bot_info.provider_domain_id)
        if client_cred is None:
            logger.warn("A client credential is not set. Please set values")
            return

        # Eco app
        installed_app = install_app_repo.get_installed_app(notice_content.user_setting.domain_id)
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
            domain_id=notice_content.user_setting.domain_id,
            access_token=res["access_token"],
            created_at=current_time,
            expired_at=current_time + int(res["expires_in"])
        )
        # Put access token
        access_token_repo.put_access_token_item(access_token_obj)

    bot_api = lineworks.bot.BotApi(access_token_obj.access_token)

    # send message
    try:
        for msg_content in msg_contents:
            res = bot_api.send_message_to_user(msg_content,
                                               bot_info.bot_id,
                                               notice_content.user_setting.user_id)
        return
    except lineworks.base.BotApiRequestError as e:
        logger.exception(e)
        logger.error("{} {} headers: {} body:{}".format(e.request.method, e.request.url, e.request.headers, e.request.body))
        logger.error("{} headers: {} body: {}".format(e.response.status_code, e.response.headers, e.response.text))


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context: LambdaContext):
    logger.info(event)
    logger.info(event.raw_event)
    logger.info(len(event.raw_event["Records"]))
    for record in event.records:
        notify(record.body)
