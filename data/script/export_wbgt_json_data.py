import os
import json
import shutil

import pandas as pd


data_dir = os.path.join(os.path.dirname(__file__), '../')
backend_data_dir = os.path.join(os.path.dirname(__file__), '../../backend/src/data')
frontend_data_dir = os.path.join(os.path.dirname(__file__), '../../frontend/src/data')

wbgt_point_csv_file_name = 'wbgt_point_data.csv'

wbgt_points_json_file_name = 'wbgt_points.json'
wbgt_pref_json_file_name = 'wbgt_pref.json'
wbgt_alert_level_json_file_name = 'wbgt_alert_levels.json'

wbgt_point_csv_path = os.path.join(data_dir, wbgt_point_csv_file_name)

wbgt_points_json_path = os.path.join(data_dir, wbgt_points_json_file_name)
wbgt_pref_json_path = os.path.join(data_dir, wbgt_pref_json_file_name)
wbgt_alert_level_json_path = os.path.join(data_dir, wbgt_alert_level_json_file_name)

backend_wbgt_points_json_path = os.path.join(backend_data_dir, wbgt_points_json_file_name)
backend_wbgt_pref_json_path = os.path.join(backend_data_dir, wbgt_pref_json_file_name)
backend_wbgt_alert_level_json_path = os.path.join(backend_data_dir, wbgt_alert_level_json_file_name)

frontend_wbgt_pref_json_path = os.path.join(frontend_data_dir, wbgt_pref_json_file_name)
frontend_wbgt_alert_level_json_path = os.path.join(frontend_data_dir, wbgt_alert_level_json_file_name)


def main():
    df = pd.read_csv(wbgt_point_csv_path, sep=",", encoding="utf-8", header=0, dtype=str)

    wbgt_points = []
    wbgt_pref_dict = {}
    for d in df.itertuples():
        wbgt_points.append(
            {
                "point_id": d.point_id,
                "point_key": d.point_key,
                "pref_key": d.pref_key,
                "point_name_ja": d.point_name_ja
            }
        )
        if d.pref_key not in wbgt_pref_dict:
            wbgt_pref_dict[d.pref_key] = {
                "pref_key": d.pref_key,
                "pref_name_ja": d.pref_name_ja,
                "points": [d.point_id]
            }
        else:
            wbgt_pref_dict[d.pref_key]["points"].append(d.point_id)

    wbgt_prefs = list(wbgt_pref_dict.values())

    with open(wbgt_points_json_path, 'w') as f:
        json.dump(wbgt_points, f, indent=4, ensure_ascii=False)

    with open(wbgt_pref_json_path, 'w') as f:
        json.dump(wbgt_prefs, f, indent=4, ensure_ascii=False)

    # copy to backend data dir
    shutil.copyfile(wbgt_points_json_path, backend_wbgt_points_json_path)
    shutil.copyfile(wbgt_pref_json_path, backend_wbgt_pref_json_path)
    shutil.copyfile(wbgt_alert_level_json_path, backend_wbgt_alert_level_json_path)

    # copy to frontend data dir
    shutil.copyfile(wbgt_pref_json_path, frontend_wbgt_pref_json_path)
    shutil.copyfile(wbgt_alert_level_json_path, frontend_wbgt_alert_level_json_path)


if __name__ == '__main__':
    main()
