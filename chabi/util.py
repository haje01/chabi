from logging import StreamHandler, Formatter
from logging.handlers import RotatingFileHandler

from flask import current_app


def init_logger(app, filename, log_level):
    formatter = Formatter('%(asctime)s %(pathname)s:%(lineno)d %(levelname)s -'
                          ' %(message)s', '%Y-%m-%d %H:%M:%S.%03d')

    handler = RotatingFileHandler('logs/{}'.format(filename), maxBytes=10000,
                                  backupCount=2)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)

    handler = StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    app.logger.addHandler(handler)


def debug(msg):
    current_app.logger.debug(msg)


def info(msg):
    current_app.logger.info(msg)


def warning(msg):
    current_app.logger.warning(msg)


def error(msg):
    current_app.logger.error(msg)


def critical(msg):
    current_app.logger.critical(msg)
