import logging
from logging import StreamHandler, Formatter
from logging.handlers import RotatingFileHandler

from flask import current_app


def init_logger(app, filename, log_level, werkzeug_log=True):
    formatter = Formatter('%(asctime)s %(pathname)s:%(lineno)d %(levelname)s -'
                          ' %(message)s', '%Y-%m-%d %H:%M:%S.%03d')

    wlog = logging.getLogger('werkzeug')
    wlog.disabled = not werkzeug_log
    if werkzeug_log:
        wlog.setLevel(log_level)

    handler = RotatingFileHandler('logs/{}'.format(filename), maxBytes=10000,
                                  backupCount=2)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)
