#logger.py#

import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "app_logging")

os.makedirs(LOG_DIR, exist_ok=True)


def setup_logger():
    logging.basicConfig(
        filename=os.path.join(LOG_DIR, "app.log"),
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    return logging.getLogger("AppLogger")


logger = setup_logger()

