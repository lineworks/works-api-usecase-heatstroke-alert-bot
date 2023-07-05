import json
import datetime
from typing import List, Dict
from io import StringIO
import requests
import pandas as pd

import urllib.request
import ssl

WBGT_DATETIME_STR_FORMAT = '%Y%m%d%H'
YOHOU_ALL_URL = "https://www.wbgt.env.go.jp/prev15WG/dl/yohou_all.csv"

class WBGTData():
    def __init__(self):
        pass

    def get_yohou_all(self) -> Dict:
        ctx = ssl.create_default_context()
        ctx.options |= 0x4  # ssl.OP_LEGACY_SERVER_CONNECT
        with urllib.request.urlopen(YOHOU_ALL_URL, context=ctx) as res:
            res_body = res.read()

        rst = res_body.decode()

        df = pd.read_csv(StringIO(rst), sep=",", encoding="ascii", index_col=0, header=0)
        df = df.fillna(0)
        df = df.drop(df.columns[[0]], axis=1)
        json_data = df.to_json()
        rst = json.loads(json_data)
        return rst


if __name__ == '__main__':
    wbgt = WBGTData()
    r = wbgt.get_yohou_all()
