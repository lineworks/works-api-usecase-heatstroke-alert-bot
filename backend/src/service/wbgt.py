from typing import List
from datetime import date


class WBGTService:
    def __init__(self):
        pass

    def create_wbgt_key(self, point_id: str, time_key: str) -> str:
        return "{}_{}".format(point_id, time_key)


    def get_daily_time_keys(self, date_key: str) -> List[str]:
        return [ "{}{:02}".format(date_key, hour) for hour in range(3, 25, 3) ]

    def convert_to_date_key(self, d: date) -> str:
        return d.strftime('%Y%m%d')


if __name__ == '__main__':
    pass
