import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler


def init_logger(app, filename, log_level, max_bytes=1048576, backup_cnt=10,
                werkzeug_log=True):
    formatter = Formatter('%(asctime)s %(pathname)s:%(lineno)d %(levelname)s -'
                          ' %(message)s', '%Y-%m-%d %H:%M:%S.%03d')

    wlog = logging.getLogger('werkzeug')
    wlog.disabled = not werkzeug_log
    if werkzeug_log:
        wlog.setLevel(log_level)

    handler = RotatingFileHandler('logs/{}'.format(filename),
                                  maxBytes=max_bytes, backupCount=backup_cnt)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)
