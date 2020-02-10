#! /usr/bin/env python3
# global logger file, import this module.

import logging

logger = logging.getLogger("capture")
logger.setLevel(logging.INFO)

stream_hander = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s: %(message)s')
stream_hander.setFormatter(formatter)
logger.addHandler(stream_hander)

file_handler = logging.FileHandler('capture.log')
logger.addHandler(file_handler)

if __name__ == '__main__':
    logger.info("logger")
