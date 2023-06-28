from typing import List, Union, Optional
from datetime import datetime

from ..models import (
    WBGT,
)
from ..datastore.wbgt import BaseWBGTRepository
from ..service.wbgt import WBGTService
from ..lib.wbgt_data import WBGTData


MAX_IMPORT_COUNT_BY_POINT = 10   # for 24h

class WBGTImporterApplication():
    def __init__(self, wbgt_repo: BaseWBGTRepository, wbgt_svc: WBGTService, wbgt_data_lib: WBGTData):
        self.wbgt_repo = wbgt_repo
        self.wbgt_svc = wbgt_svc
        self.wbgt_data_lib = wbgt_data_lib

    def load_wbgt_pred_data(self):
        current_timestamp = datetime.now().timestamp()

        newest_pred_data = []
        # Download
        data = self.wbgt_data_lib.get_yohou_all()
        count = 0
        for time_key, points in data.items():
            if count >= 8:
                break
            for point_id, value  in points.items():
                wbgt_raw = {
                    "wbgt_key": self.wbgt_svc.create_wbgt_key(point_id, time_key),
                    "point_id": point_id,
                    "time_key": time_key,
                    "value": float(value) / 10.0,  # need to divide by 10
                    "updated_timestamp": current_timestamp
                }
                wbgt = WBGT.parse_obj(wbgt_raw)
                newest_pred_data.append(wbgt)
            count += 1

        # Save
        self.wbgt_repo.put_wbgt_list(newest_pred_data)
