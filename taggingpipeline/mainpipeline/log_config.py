# logger_config.py
import os
import time

from loguru import logger

# add logger 
logdir = '/root/autodl-tmp/tmp_res/tag_log/logs'
logger.add(os.path.join(logdir, f'{time.strftime("%Y%m%d_%H%M")}_log.log'), rotation="500 MB",
           format="[{time:HH:mm:ss}] {level} - {message}")


def level_filter(level):
    def is_level(record):
        return record["level"].name == level
    return is_level
# logger.add("./logs/app.log", filter=level_filter(level="WARNING"))


def get_logger():
    return logger
