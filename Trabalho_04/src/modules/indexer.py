"""
Implementation of the indexer
"""

import logging
import os
from ast import literal_eval

import numpy as np
import pandas as pd

from modules.utils import ConfigParser, TFIDF, IndexTools

class Indexer():
    """
    Implements a indexer
    """

    def __init__(self) -> None:
        # Get configuration file instructions
        self.__config = ConfigParser("./cfg/INDEX.CFG").params()

        # Dictionary of file paths
        self.files = {
            "input": self.__config.get("LEIA"),
            "output": self.__config.get("ESCREVA")
        }

        # Run configuration check
        self.__check_config()

        # Initialize parsed input files list
        self.__input = None

        # Create base output file
        self.__output = None

        # Set '_has_run' variable
        self.__has_run = False
        logging.debug("Indexer instance created")

        # Run query processor
        self.__run()

    def export_output(self) -> None:
        """
        Export output file
        """
        logging.debug("Exporting indexer output file")
        self.__output.to_csv(self.files["output"], sep=";", index=False)
        logging.debug("Indexer output file exported")

    def __check_config(self):
        """Check validity of configuration file instructions

        Raises:
            ValueError: In case of invalid configuration file instructions
        """
        if isinstance(self.files["input"], list):
            logging.error(
                "Configuration must have only 1 'LEIA' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'LEIA' instruction"
            )
        if isinstance(self.files["output"], list):
            logging.error(
                "Configuration must have only 1 'ESCREVA' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'ESCREVA' instruction"
            )
        os.makedirs(os.path.dirname(self.files["input"]), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["output"]), exist_ok=True)

    def __run(self) -> None:
        """
        Run the indexer
        """
        if self.__has_run:
            logging.error("This indexer has already run")
            raise ValueError("This indexer has already run")
        logging.debug("Running Indexer")

        # Parse input file
        self.__input = pd.read_csv(
            self.files["input"],
            sep = ";",
            converters = {
                "RecordNumbers": literal_eval
            }
        )

        # Create 'term x document' matrix
        logging.debug("Creating Term x Document matrix")
        self.__output = IndexTools.create_term_document_matrix(self.__input, "RecordNumbers")

        # Export output file
        logging.debug("Exporting output")
        self.export_output()

        logging.debug("Indexer run finished")
        self.__has_run = True
