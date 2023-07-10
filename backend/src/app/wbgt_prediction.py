from typing import List, Union, Optional
from datetime import date

from ..models import (
    WBGT,
    WBGTPoint,
    WBGTPrefPoint,
    WBGTAlertLevel,
    UserSetting,
)
from ..datastore.wbgt import (
    BaseWBGTPointRepository,
    BaseWBGTPrefPointRepository,
    BaseWBGTAlertLevelRepository,
    BaseWBGTRepository,
)
from ..service.wbgt import WBGTService
from ..lib.wbgt_data import WBGTData


class WBGTPredictionApplication():
    def __init__(self,
                 wbgt_point_repo: BaseWBGTPointRepository,
                 wbgt_pref_point_repo: BaseWBGTPrefPointRepository,
                 wbgt_repo: BaseWBGTRepository,
                 wbgt_alert_level_repo: BaseWBGTAlertLevelRepository,
                 wbgt_svc: WBGTService
                 ):
        self.wbgt_point_repo = wbgt_point_repo
        self.wbgt_pref_point_repo = wbgt_pref_point_repo
        self.wbgt_repo = wbgt_repo
        self.wbgt_alert_level_repo = wbgt_alert_level_repo
        self.wbgt_svc = wbgt_svc

    def check_alert_level(self, wbgt: WBGT) -> Optional[WBGTAlertLevel]:
        rst = None
        wbgt_alert_levels = self.wbgt_alert_level_repo.get_wbgt_alert_levels()
        for alert_level in wbgt_alert_levels:
            if alert_level.min_value <= wbgt.value and alert_level.max_value >= wbgt.value:
                if rst is None or alert_level.priority > rst.priority:
                    rst = alert_level
        return rst

    def get_wbgt_points_of_prefecture(self, pref_key: str) -> List[WBGTPoint]:
        pref = self.wbgt_pref_point_repo.get_wbgt_pref_point(pref_key)
        if pref is None:
            return []
        point_list = []
        for wbgt_point_id in pref.points:
            point = self.wbgt_point_repo.get_wbgt_point(wbgt_point_id)
            point_list.append(point)
        return point_list

    def get_daily_wbgt_of_point(self, wbgt_point: WBGTPoint, d: date) -> List[WBGT]:
        date_key = self.wbgt_svc.convert_to_date_key(d)
        wbgt_list = []
        for time_key in self.wbgt_svc.get_daily_time_keys(date_key):
            wbgt = self.wbgt_repo.get_wbgt(self.wbgt_svc.create_wbgt_key(wbgt_point.point_id, time_key))
            if wbgt is not None:
                wbgt_list.append(wbgt)
        return wbgt_list

    def predict_daily_wbgt_of_prefecture(self, wbgt_pref: WBGTPrefPoint, d: date) -> List[WBGT]:
        wbgt_list = []
        for wbgt_point_id in wbgt_pref.points:
            wbgt_point = self.wbgt_point_repo.get_wbgt_point(wbgt_point_id)
            wbgts = self.predict_daily_wbgt_of_point(wbgt_point, d)
            for wbgt in wbgts:
                if wbgt is not None:
                    wbgt_list.append(wbgt)
        return wbgt_list

    def predict_daily_wbgt_of_point(self, wbgt_point: WBGTPoint, d: date) -> List[WBGT]:
        wbgt_list = self.get_daily_wbgt_of_point(wbgt_point, d)
        return wbgt_list

    def get_max_wbgt(self, wbgt_list: List[WBGT]) -> Union[WBGT, None]:
        max_wbgt = None
        for wbgt in wbgt_list:
            if max_wbgt is None:
                max_wbgt = wbgt
            elif max_wbgt.value < wbgt.value:
                max_wbgt = wbgt
            else:
                continue
        return max_wbgt

    def get_max_alert_level(self, alert_level_list: List[WBGTAlertLevel]) -> WBGTAlertLevel:
        max_alert_level = None
        for alert_level in alert_level_list:
            if max_alert_level is None:
                max_alert_level = alert_level
            elif max_alert_level.priority < alert_level.priority:
                max_alert_level = alert_level
            else:
                continue
        if max_alert_level is None:
            raise Exception("Alert level is None")

        return max_alert_level

    def is_notify_target(self, user_setting: UserSetting, target_alert_level: WBGTAlertLevel):
        user_alert_level = self.wbgt_alert_level_repo.get_wbgt_alert_level(user_setting.alert_level_key)
        if user_alert_level == None:
            return False
        return target_alert_level.priority >= user_alert_level.priority


if __name__ == '__main__':
    import json
    import os
    from datetime import datetime, timedelta, timezone
    from .import_wbgt import WBGTImporterApplication
    from ..datastore.wbgt import (
        InMemoryWBGTPointRepository,
        InMemoryWBGTPrefPointRepository,
        InMemoryWBGTAlertLevelRepository,
        InMemoryWBGTRepository,
    )

    current_datetime = datetime.now(timezone(timedelta(hours=9)))
    current_time = current_datetime.time()
    day = current_datetime.date()
    #day += timedelta(days=1)

    wbgt_points_json_file = os.path.join(os.path.dirname(__file__), '../data/wbgt_points.json')
    wbgt_pref_points_json_file = os.path.join(os.path.dirname(__file__), '../data/wbgt_pref.json')
    wbgt_alert_level_json_file = os.path.join(os.path.dirname(__file__), '../data/wbgt_alert_levels.json')

    with open(wbgt_points_json_file) as f:
        wbgt_points_data = json.load(f)
    wbgt_point_repo = InMemoryWBGTPointRepository(wbgt_points_data)

    with open(wbgt_pref_points_json_file) as f:
        wbgt_pref_points_data = json.load(f)
    wbgt_pref_point_repo = InMemoryWBGTPrefPointRepository(wbgt_pref_points_data)

    with open(wbgt_alert_level_json_file) as f:
        wbgt_alert_level_data = json.load(f)
    wbgt_alert_level_repo = InMemoryWBGTAlertLevelRepository(wbgt_alert_level_data)

    wbgt_repo = InMemoryWBGTRepository()

    wbgt_svc = WBGTService()

    wbgt_data_lib = WBGTData()

    # load wbgt points
    wbgt_importer = WBGTImporterApplication(wbgt_repo, wbgt_svc, wbgt_data_lib)
    wbgt_importer.load_wbgt_pred_data()

    # daily prediction
    wbgt_pred_service = WBGTPredictionApplication(wbgt_point_repo, wbgt_pref_point_repo, wbgt_repo, wbgt_alert_level_repo, wbgt_svc)
    wbgt_points = wbgt_pred_service.get_wbgt_points_of_prefecture("osaka")
    alert_level_list = []
    for point in wbgt_points:
        print(point)
        wbgt_list = wbgt_pred_service.predict_daily_wbgt_of_point(point, day)
        max_wbgt = wbgt_pred_service.get_max_wbgt(wbgt_list)
        print(max_wbgt)
        if max_wbgt is not None:
            alert_level = wbgt_pred_service.check_alert_level(max_wbgt)
            alert_level_list.append(alert_level)
    rst = wbgt_pred_service.get_max_alert_level(alert_level_list)
    print(rst)
