from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
import datetime


class AccessToken(BaseModel):
    domain_id: str
    access_token: str
    created_at: int
    expired_at: int


class BotClientCredential(BaseModel):
    bot_id: str
    domain_id: str
    client_id: str
    client_secret: str
    service_account: str
    private_key: str


class BotInfo(BaseModel):
    bot_id: str
    provider_domain_id: str
    bot_secret: str


class InstalledApp(BaseModel):
    domain_id: str
    service_account: str
    ver: str


class WBGTPoint(BaseModel):
    point_id: str
    point_key: str
    pref_key: str
    point_name_ja: str


class WBGTPrefPoint(BaseModel):
    pref_key: str
    pref_name_ja: str
    points: List[str]


class WBGTAlertLevel(BaseModel):
    alert_level_key: str
    min_value: int
    max_value: int
    priority: int
    alert_level_title_ja: str
    alert_level_subtitle_ja: str
    alert_level_description_ja: str
    alert_level_background_color: str
    alert_level_text_color: str


class WBGT(BaseModel):
    wbgt_key: str  # {point_id}_{time_key}
    point_id: str
    time_key: str  # yyyymmddhh   *hh: 01-24 (e.g. 2023061424)
    value: float
    updated_timestamp: int  # unix time


class UserSetting(BaseModel):
    user_id: str
    domain_id: str
    pref_key: str
    alert_level_key: str


class NoticeList(BaseModel):
    pref_key: str
    user_settings: List[UserSetting]


class NoticeContentPoint(BaseModel):
    point: WBGTPoint
    max_wbgt: WBGT


class NoticeContent(BaseModel):
    day: datetime.date
    points: List[NoticeContentPoint]
    alert_level: WBGTAlertLevel
    prefecture: WBGTPrefPoint
    user_setting: UserSetting

