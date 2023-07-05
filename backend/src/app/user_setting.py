from typing import List, Dict, Union, Optional
from datetime import date

from ..models import (
    WBGT,
    WBGTPoint,
    WBGTPrefPoint,
    WBGTAlertLevel,
    UserSetting,
)
from ..datastore.wbgt import (
    BaseWBGTAlertLevelRepository,
)
from ..datastore.user_setting import (
    BaseUserSettingRepository,
)
from ..service.wbgt import WBGTService
from ..lib.wbgt_data import WBGTData


class UserSettingApplication():
    def __init__(self,
                 user_setting_repo: BaseUserSettingRepository,
                 ):
        self.user_setting_repo = user_setting_repo

    def get_all_user_settings(self) -> List[UserSetting]:
        return self.user_setting_repo.get_all_user_settings()

    def get_user_settings(self, user_id: str) -> Optional[UserSetting]:
        return self.user_setting_repo.get_user_setting(user_id)

    def put_user_settings(self, user_setting: UserSetting):
        self.user_setting_repo.put_user_setting(user_setting)

    def delete_user_settings_w_domain_id(self, domain_id: str):
        self.user_setting_repo.delete_user_setting_w_domain_id(domain_id)

    def classify_user_setting_into_prefecture(self) -> Dict[str, List[UserSetting]]:
        users_pref = {}
        user_settings = self.get_all_user_settings()

        for user_s in user_settings:
            if user_s.pref_key in users_pref:
                users_pref[user_s.pref_key].append(user_s)
            else:
                users_pref[user_s.pref_key] = [user_s]

        return users_pref
