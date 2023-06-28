from abc import abstractmethod
from .base import BaseClass
from typing import List, Dict, Optional
from ..models import (
    WBGT,
    WBGTPoint,
    WBGTPrefPoint,
    WBGTAlertLevel,
)
from ..lib.aws import dynamodb


class BaseWBGTPrefPointRepository(BaseClass):
    @abstractmethod
    def get_wbgt_pref_point(self, pref_key: str) -> WBGTPrefPoint:
        pass

    @abstractmethod
    def get_wbgt_pref_points(self) -> List[WBGTPrefPoint]:
        pass


class InMemoryWBGTPrefPointRepository(BaseWBGTPrefPointRepository):
    def __init__(self, data: List[Dict]):
        self.wbgt_pref_points = {}
        for d in data:
            self.wbgt_pref_points[d["pref_key"]] = WBGTPrefPoint.parse_obj(d)

    def get_wbgt_pref_point(self, pref_key: str) -> WBGTPrefPoint:
        return self.wbgt_pref_points.get(pref_key)

    def get_wbgt_pref_points(self) -> List[WBGTPrefPoint]:
        return list(self.wbgt_pref_points.values())


class BaseWBGTPointRepository(BaseClass):
    @abstractmethod
    def get_wbgt_points(self) -> List[WBGTPoint]:
        pass

    @abstractmethod
    def get_wbgt_point(self, point_id: str) -> WBGTPoint:
        pass


class InMemoryWBGTPointRepository(BaseWBGTPointRepository):
    def __init__(self, data: List[Dict]):
        self.wbgt_points = {}
        for d in data:
            self.wbgt_points[d["point_id"]] =  WBGTPoint.parse_obj(d)

    def get_wbgt_point(self, point_id: str) -> WBGTPoint:
        return self.wbgt_points.get(point_id)

    def get_wbgt_points(self) -> List[WBGTPoint]:
        return list(self.wbgt_points.values())


class BaseWBGTAlertLevelRepository(BaseClass):
    @abstractmethod
    def get_wbgt_alert_levels(self) -> List[WBGTAlertLevel]:
        pass

    @abstractmethod
    def get_wbgt_alert_level(self, alert_level_key) -> Optional[WBGTAlertLevel]:
        pass


class InMemoryWBGTAlertLevelRepository(BaseWBGTAlertLevelRepository):
    def __init__(self, data: List[Dict]):
        self.wbgt_alert_levels = {}
        for d in data:
            self.wbgt_alert_levels[d["alert_level_key"]] =  WBGTAlertLevel.parse_obj(d)

    def get_wbgt_alert_levels(self) -> List[WBGTAlertLevel]:
        return list(self.wbgt_alert_levels.values())

    def get_wbgt_alert_level(self, alert_level_key) -> Optional[WBGTAlertLevel]:
        return self.wbgt_alert_levels.get(alert_level_key)


class BaseWBGTRepository(BaseClass):
    @abstractmethod
    def get_wbgt(self, wbgt_key: str) -> Optional[WBGT]:
        pass

    @abstractmethod
    def put_wbgt_list(self, wbgt_list: List[WBGT]):
        pass

    @abstractmethod
    def put_wbgt(self, wbgt: WBGT):
        pass


class InMemoryWBGTRepository(BaseWBGTRepository):
    def __init__(self):
        self.clear()

    def clear(self):
        self.wbgt_list = {}

    def get_wbgt(self, wbgt_key: str) -> Optional[WBGT]:
        return self.wbgt_list.get(wbgt_key)

    def put_wbgt_list(self, wbgt_list: List[WBGT]):
        for w in wbgt_list:
            self.put_wbgt(w)

    def put_wbgt(self, wbgt: WBGT):
        self.wbgt_list[wbgt.wbgt_key] = wbgt


class DynamoDBWBGTRepository(BaseWBGTRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name

    def get_wbgt(self, wbgt_key: str) -> Optional[WBGT]:
        wbgt_raw = dynamodb.get_item(self.table_name, {"wbgt_key": wbgt_key})
        if wbgt_raw is not None:
            return WBGT.parse_obj(wbgt_raw)

    def put_wbgt_list(self, wbgt_list: List[WBGT]):
        items = []
        for w in wbgt_list:
            items.append(w.dict())
        dynamodb.write_batch(self.table_name, items)

    def put_wbgt(self, wbgt: WBGT):
        dynamodb.put_item(self.table_name, wbgt.dict())

