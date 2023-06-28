from abc import abstractmethod
from .base import BaseClass
from typing import List, Dict, Optional
from ..models import (
    UserSetting,
)
from ..lib.aws import dynamodb


class BaseUserSettingRepository(BaseClass):
    @abstractmethod
    def get_user_setting(self, user_id: str) -> Optional[UserSetting]:
        pass

    @abstractmethod
    def get_all_user_settings(self) -> List[UserSetting]:
        pass

    @abstractmethod
    def put_user_setting(self, user_setting: UserSetting):
        pass


class InMemoryUserSettingRepository(BaseUserSettingRepository):
    def __init__(self, data: List[Dict]):
        self.user_settings = {}
        for d in data:
            self.user_settings[d["user_id"]] = UserSetting.parse_obj(d)

    def get_user_setting(self, user_id: str) -> Optional[UserSetting]:
        return self.user_settings.get(user_id)

    def get_all_user_settings(self) -> List[UserSetting]:
        return list(self.user_settings.values())

    def put_user_setting(self, user_setting: UserSetting):
        self.user_settings[user_setting.user_id] = UserSetting.parse_obj(user_setting)

class DynamoDBUserSettingRepository(BaseUserSettingRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name

    def get_user_setting(self, user_id: str) -> Optional[UserSetting]:
        user_setting_raw = dynamodb.get_item(self.table_name, {"user_id": user_id})
        if user_setting_raw is not None:
            return UserSetting.parse_obj(user_setting_raw)

    def get_all_user_settings(self) -> List[UserSetting]:
        user_settings_raw = dynamodb.get_items(self.table_name)
        user_setting_list = []
        for user_setting_raw in user_settings_raw:
            if user_setting_raw is not None:
                user_setting_list.append(UserSetting.parse_obj(user_setting_raw))
        return user_setting_list

    def put_user_setting(self, user_setting: UserSetting):
        dynamodb.put_item(self.table_name, user_setting.dict())
