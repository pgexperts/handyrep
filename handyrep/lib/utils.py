from fabric.api import execute, sudo, run, env, task
from fabric.network import disconnect_all
from fabric.contrib.files import upload_template
from lib.config import ReadConfig
from lib.error import CustomError
import json
from datetime import datetime, timedelta
import logging
import time
import importlib
from plugins.failplugin import failplugin

class HandyRepUtils(Object):

    def __init__(self, conf, servers):
        self.conf = configdict

    