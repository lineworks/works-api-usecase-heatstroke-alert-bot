import os
import json
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta, time, timezone

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
from .datastore.user_setting import (
    DynamoDBUserSettingRepository,
)
from .service.wbgt import (
    WBGTService
)
from .app.wbgt_prediction import (
    WBGTPredictionApplication,
)
from .app.user_setting import (
    UserSettingApplication
)

from .service.publisher import SQSMessagePublisher
from .models import (
    NoticeList,
    NoticeContentPoint,
    NoticeContent,
    AccessToken,
    BotClientCredential,
)
from .service.publisher import SQSMessagePublisher

logger = Logger()


def notice_list(message: str):
    wbgt_table_name = os.environ.get("TABLE_WBGT")
    if wbgt_table_name is None:
        raise Exception("Please set TABLE_WBGT env")

    queue_notify_alert_name = os.environ.get("QUEUE_NOTIFY_ALERT")
    if queue_notify_alert_name is None:
        raise Exception("Please set QUEUE_NOTIFY_ALERT env")

    notice_list = NoticeList.parse_raw(message)

    current_datetime = datetime.now(timezone(timedelta(hours=9)))
    current_time = current_datetime.time()
    day = current_datetime.date()

    base = time(15, 0, 0)
    if current_time >= base:
        # get data of next day
        day += timedelta(days=1)

    wbgt_svc = WBGTService()

    wbgt_points_json_file = os.path.join(os.path.dirname(__file__), 'data/wbgt_points.json')
    wbgt_pref_points_json_file = os.path.join(os.path.dirname(__file__), 'data/wbgt_pref.json')
    wbgt_alert_level_json_file = os.path.join(os.path.dirname(__file__), 'data/wbgt_alert_levels.json')

    with open(wbgt_points_json_file) as f:
        wbgt_points_data = json.load(f)
    wbgt_point_repo = InMemoryWBGTPointRepository(wbgt_points_data)

    with open(wbgt_pref_points_json_file) as f:
        wbgt_pref_points_data = json.load(f)
    wbgt_pref_point_repo = InMemoryWBGTPrefPointRepository(wbgt_pref_points_data)

    with open(wbgt_alert_level_json_file) as f:
        wbgt_alert_level_data = json.load(f)
    wbgt_alert_level_repo = InMemoryWBGTAlertLevelRepository(wbgt_alert_level_data)

    wbgt_repo = DynamoDBWBGTRepository(wbgt_table_name)

    wbgt_svc = WBGTService()
    wbgt_pred_service = WBGTPredictionApplication(wbgt_point_repo, wbgt_pref_point_repo, wbgt_repo, wbgt_alert_level_repo, wbgt_svc)

    # daily prediction
    wbgt_pref = wbgt_pref_point_repo.get_wbgt_pref_point(notice_list.pref_key)
    logger.info(wbgt_pref)
    if wbgt_pref is None:
        raise Exception("WBGT data is null.")
    wbgt_points = wbgt_pred_service.get_wbgt_points_of_prefecture(notice_list.pref_key)
    logger.info(wbgt_points)

    alert_level_list = []
    point_and_wbgt_list = []
    for point in wbgt_points:
        logger.info(point)
        wbgt_list = wbgt_pred_service.predict_daily_wbgt_of_point(point, day)
        logger.info(wbgt_list)
        max_wbgt = wbgt_pred_service.get_max_wbgt(wbgt_list)
        if max_wbgt is not None:
            alert_level = wbgt_pred_service.check_alert_level(max_wbgt)
            alert_level_list.append(alert_level)
            point_and_wbgt_list.append(
                NoticeContentPoint(
                    point=point,
                    max_wbgt=max_wbgt,
                )
            )
    logger.info(alert_level_list)
    logger.info(point_and_wbgt_list)
    if len(alert_level_list) == 0:
        raise Exception("Alert level is None")

    max_alert_level = wbgt_pred_service.get_max_alert_level(alert_level_list)

    message_publisher = SQSMessagePublisher(queue_notify_alert_name)
    # Notify
    for user_setting in notice_list.user_settings:
        if wbgt_pred_service.is_notify_target(user_setting, max_alert_level):
            notice_content = NoticeContent(
                day=day,
                points=point_and_wbgt_list,
                alert_level=max_alert_level,
                prefecture=wbgt_pref,
                user_setting=user_setting,
            )
            logger.info(notice_content)
            message_publisher.publish(notice_content.json())


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context: LambdaContext):
    logger.info(event)
    logger.info(event.raw_event)
    logger.info(len(event.raw_event["Records"]))
    for record in event.records:
        logger.info("MessageID: {}".format(record.message_id))
        notice_list(record.body)
