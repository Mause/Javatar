from os.path import join, exists

import sublime
import threading
import urllib
import hashlib
import traceback
from .javatar_thread import SilentThreadProgress
from .javatar_utils import (
    get_startup_time, get_settings, is_debug, set_settings
)


USAGE_VERSION = "0.1"
PACKAGES_STATS = "http://javatar.digitalparticle.com/"


def get_usage_version():
    return USAGE_VERSION


def get_usage_data():
    from .javatar_news import get_version
    from .javatar_utils import get_settings
    return {
        "SchemaVersion": get_usage_version(),
        "JavatarVersion": get_version(),
        "JavatarChannel": str.lower(get_settings("package_channel")),
        "JavatarDebugMode": str.lower(str(get_settings("debug_mode"))),
        "JavatarAsPackage": str.lower(str(exists(join(sublime.installed_packages_path(), "Javatar.sublime-package")))),
        "JavatarStartupTime": "{0:.2f}s".format(get_startup_time()),
        "JavatarNews": str(get_settings("message_id")),
        "JavatarActionHistory": str.lower(str(get_settings("enable_actions_history"))),
        "JavatarSendUsage": str.lower(str(get_settings("send_stats_and_usages"))),
        "SublimeVersion": str(sublime.version()),
        "Platform": sublime.platform(),
    }


def send_usages(params=None, lasttime=False):
    params = params or {}

    if get_settings("send_stats_and_usages"):
        params["usage"] = "true"
        thread = JavatarPackageUsageThread(params, lasttime)
        thread.start()
        SilentThreadProgress(thread, send_usage_complete)


def send_usage_complete(thread):
    if thread.result:
        if thread.lasttime:
            if is_debug():
                print("Javatar usage data sent as last time: " + thread.data)
            set_settings("javatar_gp", get_settings("javatar_gp") | 0x1)
        else:
            if is_debug():
                print("Javatar usage data sent: " + thread.data)
            set_settings("javatar_gp", get_settings("javatar_gp") & (~0x1))


class JavatarPackageUsageThread(threading.Thread):
    def __init__(self, params=None, lasttime=False):
        self.lasttime = lasttime
        self.params = params or {}
        threading.Thread.__init__(self)

    def run(self):
        try:
            urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler()))
            url = PACKAGES_STATS + "?" + urllib.parse.urlencode(self.params)
            data = urllib.request.urlopen(url).read()
            self.data = str(data)
            self.datahash = hashlib.sha256(self.data.encode("utf-8")).hexdigest()
            self.result = True
        except Exception as e:
            if is_debug():
                print("Javatar Usage Error: " + str(e))
                traceback.print_exc()
            self.result = False
