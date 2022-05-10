"""
Main program of the project
"""

import os
import sys
import logging
from datetime import datetime as dt

from modules.query_processor import QueryProcessor
from modules.inverse_list import InverseListGenerator
from modules.indexer import Indexer


if __name__ == "__main__":
    # Change execution path to main.py directory
    os.chdir(os.path.dirname(__file__))

    # Create log folder
    os.makedirs("./log", exist_ok=True)

    # Logger configuration
    LOG_NAME = dt.utcnow().strftime("%Y-%m-%d_%Hh%Mm%Ss.%f")[:-3]
    LOG_FORMAT = "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s"
    stream_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
        handlers=[
            logging.FileHandler(f"./log/{LOG_NAME}.log"),
            stream_handler
        ]
    )

    # Instantiate and run query processor
    query_processor = QueryProcessor()

    # Instantiate and run inverse list generator
    inverse_list_generator = InverseListGenerator()

    # Instantiate and run indexer
    indexer = Indexer()
