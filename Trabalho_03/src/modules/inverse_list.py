"""
Implementation of the query processor
"""

import logging
import os
from xml.dom import minidom

from modules.utils import ConfigParser, FileXML


class InverseListGenerator():
    """
    Implements a inverse list generator
    """

    def __init__(self) -> None:
        # Get configuration file instructions
        self._config = ConfigParser("./cfg/GLI.CFG").params()

        # Dictionary of file paths
        self.files = {
            "inputs": self._config.get("LEIA"),
            "output": self._config.get("ESCREVA")
        }

        # Run configuration check
        self._check_config()

        # Initialize parsed input files list
        self._inputs = []

        # Create base output file
        self._output = ""

        # Set '_has_run' variable
        self._has_run = False
        logging.debug("Inverse list generator instance created")

        # Run query processor
        self._run()

    def _run(self) -> None:
        """
        Run the query processor
        """
        if self._has_run:
            logging.error("This inverse list generator has already run")
            raise ValueError("This inverse list generator has already run")
        logging.debug("Running InverseList")

        # Parse input files
        if isinstance(self.files["inputs"], str):
            self._inputs.append(minidom.parse(self.files["inputs"]))
        else:
            for file in self.files["inputs"]:
                self._inputs.append(minidom.parse(file))
        logging.debug("Inverse list generator run finished")
        self._has_run = True

    def _check_config(self):
        """Check validity of configuration file instructions

        Raises:
            ValueError: In case of invalid configuration file instructions
        """
        if isinstance(self.files["output"], list):
            logging.error(
                "Configuration must have only 1 'ESCREVA' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'ESCREVA' instruction"
            )
        if isinstance(self.files["inputs"], str):
            os.makedirs(os.path.dirname(self.files["inputs"]), exist_ok=True)
        else:
            for file in self.files["inputs"]:
                os.makedirs(os.path.dirname(file), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["output"]), exist_ok=True)
