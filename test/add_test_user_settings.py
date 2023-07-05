import requests
import os
import json
import urllib.parse

test_dir = os.path.dirname(__file__)
TEST_USER_LIST_JSON_NAME = os.path.join(test_dir, "test_user_list.json")


PREF_KEY = "osaka"
ALERTLEVEL_KEY = "almost_safe"

user_setting_api_url = os.environ.get("USER_SET_API_URL")
if user_setting_api_url is None:
    print("Please set USER_SET_API_URL env")
    exit()

with open(TEST_USER_LIST_JSON_NAME) as f:
    user_list = json.load(f)


cnt = 0
for user in user_list:
    print(cnt)
    user_set = {
        "user_id": user["userId"],
        "domain_id": user["domainId"],
        "pref_key": PREF_KEY,
        "alert_level_key": ALERTLEVEL_KEY
    }

    res = requests.put(urllib.parse.urljoin(user_setting_api_url,'/user_setting/{}'.format(user["userId"])), json=user_set)
    print(res.status_code)
    cnt += 1
