# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import TimedRotatingFileHandler


def logInit(log_file, loglevel=logging.INFO, consoleshow=False, backup_count=0):
    dirname, filename = os.path.split(log_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    fileTimeHandler = logging.FileHandler(log_file)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    fileTimeHandler.setFormatter(formatter)
    logging.getLogger('').addHandler(fileTimeHandler)
    logging.getLogger('').setLevel(loglevel)
    if consoleshow:
      console = logging.StreamHandler()
      console.setLevel(loglevel)
      console.setFormatter(formatter)
      logging.getLogger('').addHandler(console)

