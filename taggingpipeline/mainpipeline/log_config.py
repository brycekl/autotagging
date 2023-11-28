# logger_config.py
from loguru import logger
import os 
import time 

# add logger 
logdir = '/root/autodl-tmp/tmp_res/tag_log/logs'
logger.add(os.path.join(logdir,f'{time.strftime("%Y%m%d_%H%M")}_log.log'), rotation="500 MB",format="[{time:HH:mm:ss}] {level} - {message}")


def get_logger():
    return logger
