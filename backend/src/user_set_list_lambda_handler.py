import os
import json
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import event_source, EventBridgeEvent


from .datastore.wbgt import (
    DynamoDBWBGTRepository,
    InMemoryWBGTPointRepository,
    InMemoryWBGTPrefPointRepository,
    InMemoryWBGTAlertLevelRepository,
)
from .datastore.user_setting import (
    DynamoDBUserSettingRepository,
)
from .app.user_setting import (
    UserSettingApplication
)

from .service.publisher import SQSMessagePublisher
from .models import NoticeList

logger = Logger()

QUEUE_BATCH_SIZE = 500


def user_setting_list():
    table_name = os.environ.get("TABLE_USER_SETTING")
    if table_name is None:
        raise Exception("Please set TABLE_USER_SETTING env")
    queue_notice_list_name = os.environ.get("QUEUE_NOTICE_LIST")
    if queue_notice_list_name is None:
        raise Exception("Please set QUEUE_NOTICE_LIST env")

    user_setting_repo = DynamoDBUserSettingRepository(table_name)

    user_setting_app = UserSettingApplication(user_setting_repo)
    user_pref_list = user_setting_app.classify_user_setting_into_prefecture()

    message_publisher = SQSMessagePublisher(queue_notice_list_name)
    # send to SQS queue
    for key, user_settings in user_pref_list.items():
        logger.info("Prefecture: {}".format(key))
        logger.info("User Settings count: {}".format(len(user_settings)))

        cnt = 0
        while True:
            items = user_settings[QUEUE_BATCH_SIZE * cnt:QUEUE_BATCH_SIZE * (cnt + 1)]
            logger.info("Count: {}, Window: {}, Size: {}".format(cnt, QUEUE_BATCH_SIZE * cnt, len(items)))

            notice_list = NoticeList(
                pref_key=key,
                user_settings=items,
            )
            logger.info(notice_list)
            message_publisher.publish(notice_list.json())

            cnt += 1
            next_items = user_settings[QUEUE_BATCH_SIZE * (cnt * 1):QUEUE_BATCH_SIZE * (cnt + 2)]
            if len(next_items) < 1:
                break


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
@event_source(data_class=EventBridgeEvent)
def lambda_handler(event: EventBridgeEvent, context: LambdaContext):
    logger.info(event)
    user_setting_list()
