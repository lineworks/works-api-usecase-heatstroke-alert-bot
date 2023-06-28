import os
import urllib.parse
import json

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import LambdaFunctionUrlResolver, Response, content_types, CORSConfig
from aws_lambda_powertools.event_handler.exceptions import (
    NotFoundError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

from .models import UserSetting
from .datastore.user_setting import (
    DynamoDBUserSettingRepository,
)
from .app.user_setting import (
    UserSettingApplication
)

logger = Logger()

cors_config = CORSConfig()
#app = LambdaFunctionUrlResolver(cors=cors_config)
app = LambdaFunctionUrlResolver()


@app.get("/")
def get_index():
    logger.info(app.current_event.headers)
    logger.info(app.current_event.query_string_parameters)

    return {}


@app.get("/user_setting/<user_id>")
def get_user_setting(user_id: str):
    logger.info(app.current_event.headers)
    logger.info(app.current_event.query_string_parameters)

    table_name = os.environ.get("TABLE_USER_SETTING")
    if table_name is None:
        raise Exception("Please set TABLE_USER_SETTING env")

    user_setting_repo = DynamoDBUserSettingRepository(table_name)
    user_setting_app = UserSettingApplication(user_setting_repo)

    user_setting = user_setting_app.get_user_settings(user_id)

    if user_setting is not None:
        return json.loads(user_setting.json())
    else:
        raise NotFoundError


@app.put("/user_setting/<user_id>")
def put_user_setting(user_id: str):
    logger.info(app.current_event.headers)
    logger.info(app.current_event.body)
    logger.info(app.current_event.decoded_body)
    logger.info(app.current_event.query_string_parameters)

    user_setting_raw: dict = app.current_event.json_body
    user_setting = UserSetting.parse_obj(user_setting_raw)

    table_name = os.environ.get("TABLE_USER_SETTING")
    if table_name is None:
        raise Exception("Please set TABLE_USER_SETTING env")

    user_setting_repo = DynamoDBUserSettingRepository(table_name)
    user_setting_app = UserSettingApplication(user_setting_repo)

    user_setting_app.put_user_settings(user_setting)

    return json.loads(user_setting.json())


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(event)
    return app.resolve(event, context)
