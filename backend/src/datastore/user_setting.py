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

    @abstractmethod
    def delete_user_setting_w_domain_id(self, domain_id):
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

    def delete_user_setting_w_domain_id(self, domain_id):
        for k in self.user_settings.keys():
            if self.user_settings[k].domain_id == domain_id:
                del self.user_settings[k]


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

    def delete_user_setting_w_domain_id(self, domain_id):
        user_settings_raw = dynamodb.query(self.table_name, {"domain_id": domain_id}, "DomainId")
        keys = []
        for user_setting_raw in user_settings_raw:
            if user_setting_raw is not None:
                user_setting = UserSetting.parse_obj(user_setting_raw)
                keys.append({"user_id": user_setting.user_id})
        # delete
        dynamodb.delete_items(self.table_name, keys)
