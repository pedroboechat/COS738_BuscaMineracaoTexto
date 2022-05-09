"""
Implementation of the inverse list generator
"""

import logging
import os
import re
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
        self._output = "Word;RecordNumbers"

        # Set '_has_run' variable
        self._has_run = False
        logging.debug("Inverse list generator instance created")

        # Run query processor
        self._run()

    def export_output(self) -> None:
        """
        Export output file
        """
        logging.debug("Exporting inverse list output file")
        with open(self.files["output"], mode="w", encoding="utf-8") as file:
            file.write(self._output)
        logging.debug("Inverse list output file exported")

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

        # Create words dictionary
        words_dict = {}

        # Extract data from inputs
        logging.debug("Extracting data from input(s)")
        for xml in self._inputs:
            records_dict = FileXML.get_records_data(xml)
            for record_num, abstract in records_dict.items():
                text = re.sub(
                    r"[.,;:()%]",
                    "",
                    abstract
                )
                for word in text.split():
                    if word.isdigit():
                        continue
                    try:
                        words_dict[word].append(record_num)
                    except KeyError:
                        words_dict[word] = [record_num]

        # Sort dictionary by occurences
        logging.debug("Sorting words dictionary")
        sorted_words_dict = {
            item: words_dict[item] for item in sorted(
                words_dict,
                key = lambda x: len(words_dict[x]),
                reverse = True
            )
        }

        # Save information to output
        logging.debug("Creating output")
        for word, occurences in sorted_words_dict.items():
            self._output += f"\n{word};{occurences}"

        # Export output file
        logging.debug("Exporting output")
        self.export_output()

        logging.debug("Inverse list generator run finished")
        self._has_run = True
