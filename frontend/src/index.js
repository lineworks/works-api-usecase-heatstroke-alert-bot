import pref_list from './data/wbgt_pref.json'
import alert_level_list from './data/wbgt_alert_levels.json'

// Template variable
const woffId = process.env.WOFF_ID;
const userSettingApiUri = process.env.USER_SET_API_URL;


const setPrefectureOptions = () => {
    let sel = document.getElementById("selectPrefecture");
    let defOpt = document.createElement("option");
    defOpt.value = "default";
    defOpt.text = "設定してください";
    defOpt.defaultSelected = true;
    sel.add(defOpt)

    // set prefectures
    for(let pref of pref_list) {
        let opt = document.createElement("option");
        opt.value = pref.pref_key;
        opt.text = pref.pref_name_ja;
        sel.add(opt)
    }
};


const selectPrefectureOption = (pref_key) => {
    let sel = document.getElementById("selectPrefecture");
    let opts = sel.options;

    for(let opt of opts) {
        if (opt.value === pref_key) {
            opt.selected = true;
        } else {
            opt.selected = false;
        }
    }
};

const setAlertLevelOptions = () => {
    let sel = document.getElementById("selectAlertLevel");
    let defOpt = document.createElement("option");
    defOpt.value = "default";
    defOpt.text = "設定してください";
    defOpt.defaultSelected = true;
    sel.add(defOpt)

    // set prefectures
    for(let alert_level of alert_level_list) {
        let opt = document.createElement("option");
        opt.value = alert_level.alert_level_key;
        if (alert_level.alert_level_subtitle_ja) {
            opt.text = alert_level.alert_level_title_ja + ' | ' + alert_level.alert_level_subtitle_ja;
        } else {
            opt.text = alert_level.alert_level_title_ja;
        }
        sel.add(opt)
    }
};


const selectAlertLevelOption = (alert_level_key) => {
    let sel = document.getElementById("selectAlertLevel");
    let opts = sel.options;

    for(let opt of opts) {
        if (opt.value === alert_level_key) {
            opt.selected = true;
        } else {
            opt.selected = false;
        }
    }
};

const getUserSetting = (userId) => {
    return new Promise((resolve, reject) => {
        const url = new URL(`/user_setting/${userId}`, userSettingApiUri);
        console.log(url)

        axios.get(url.toString())
            .then((res) => {
                console.log(res)
                resolve(res.data)
            })
            .catch((err) => {
                if (err.response) {
                    if (err.response.status == 404) {
                        resolve(null)
                        return
                    } else {
                        console.log(err.response.data);
                        console.log(err.response.status);
                        console.log(err.response.headers);
                    }
                } else if (err.request) {
                    console.log(err.request);
                } else {
                    console.log('Error', err.message);
                }
                console.log(err.config);
                reject(err)
            });
    })
}


const putUserSetting = (userId, domainId,  prefKey, alertLevelKey) => {
    return new Promise((resolve, reject) => {
        const url = new URL(`/user_setting/${userId}`, userSettingApiUri);
        console.log(url)

        let user_setting = {
            "user_id": userId,
            "domain_id": domainId,
            "pref_key": prefKey,
            "alert_level_key": alertLevelKey
        }

        console.log(user_setting)

        axios.put(url.toString(), user_setting)
            .then((res) => {
                console.log(res)
                resolve(res.data)
            })
            .catch((err) => {
                console.log("error")
                console.log(err);
                reject(err)
            });
    })
}


/**
* Get WOFF info
*/
const getWoffInfo = () => {
    return {
        "language": woff.getLanguage(),
        "sdkVersion": woff.getVersion(),
        "worksVersion": woff.getWorksVersion(),
        "isInClient": woff.isInClient(),
        "isLoggedIn": woff.isLoggedIn(),
        "OS": woff.getOS(),
        "context": woff.getContext(),
    };
}


/**
 * Get profile
 */
const getProfile = () => {
    return new Promise((resolve, reject) => {
        // Get profile
        woff.getProfile().then((profile) => {
            // Success
            console.log(profile)
            resolve(profile)
        }).catch((err) => {
            // Error
            console.log(err)
            reject(err)
        });
    });
}

const registerLoginButtonHandlers = () => {
    // login call, only when external browser is used
    document.getElementById('woffLoginButton').addEventListener('click', () => {
        if (!woff.isLoggedIn()) {
            woff.login();
        }
    });

    // logout call only when external browse
    document.getElementById('woffLogoutButton').addEventListener('click', () => {
        if (woff.isLoggedIn()) {
            woff.logout();
            window.location.reload();
        }
    });
}


const registerSubmitButtonHandlers = (userId, domainId) => {
    document.getElementById('buttonSubmit').addEventListener('click', () => {
        let selPref = document.getElementById("selectPrefecture");
        let selAlertLevel = document.getElementById("selectAlertLevel");

        const prefKey = selPref.value
        const alertLevelKey = selAlertLevel.value

        if (prefKey === "default") {
            window.alert("都道府県を選択してください。");
            return;
        } else if (alertLevelKey === "default") {
            window.alert("通知する暑さ指数を選択してください。");
            return;
        }

        putUserSetting(userId, domainId, prefKey, alertLevelKey)
            .then((res) => {
                console.log(res)
                window.alert("登録しました。");
                if (woff.isInClient()) {
                    woff.closeWindow();
                }
            })
            .catch((err) => {
                // Error
                window.alert(err);
                console.error(err)
            });
    });
}


const woffInit = (woffId) => {
    if (!woffId) {
        //document.getElementById("woffAppContent").hidden = true;
    } else {
        // Initialize WOFF
        woff.init({ woffId: woffId })
            .then(() => {
                console.log(getWoffInfo())

                if (!woff.isInClient()) {
                    document.getElementById("groupWoffLoginButtons").hidden = false;
                }

                if (woff.isLoggedIn()) {
                    document.getElementById('woffLoginButton').disabled = true;
                    // Success
                    // Get and show user profile
                    getProfile()
                        .then((profile) => {
                            console.log(profile);
                            // Button handler
                            registerSubmitButtonHandlers(profile.userId, profile.domainId);

                            // Set settings
                            getUserSetting(profile.userId)
                                .then((user_setting) => {
                                    console.log(user_setting)
                                    if (user_setting !== null) {
                                        // Show settings
                                        selectPrefectureOption(user_setting.pref_key)
                                        selectAlertLevelOption(user_setting.alert_level_key)

                                    }
                                    // show settings
                                    document.getElementById("settingArea").hidden = false;
                                    document.getElementById("loadingArea").hidden = true;
                                })
                                .catch((err) => {
                                    console.log(err)
                                    window.alert(err);
                                });

                        })
                        .catch((err) => {
                            window.alert(err);
                        });

                } else {
                    document.getElementById('woffLogoutButton').disabled = true;
                }
            })
            .catch((err) => {
                // Error
                window.alert(err);
                console.error(err)
            });
    }
}

// On load
window.addEventListener('load', () => {
    console.log(woffId);
    setPrefectureOptions();
    setAlertLevelOptions();

    registerLoginButtonHandlers()

    woffInit(woffId);
});
