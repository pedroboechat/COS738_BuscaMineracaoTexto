"""
Implementation of the inverse list generator
"""

import logging
import os
from xml.dom import minidom

from modules.utils import ConfigParser, FileXML, ILGTools

class InverseListGenerator():
    """
    Implements a inverse list generator
    """

    def __init__(self) -> None:
        # Get configuration file instructions
        self.__config = ConfigParser("./cfg/GLI.CFG").params()

        # Add use_stemmer propriety
        self.__use_stemmer = not self.__config.get("STEMMER") is None

        # Dictionary of file paths
        self.files = {
            "inputs": self.__config.get("LEIA")
        }
        if self.__use_stemmer:
            self.files["output"] = self.__config.get("STEMMER")
        else:
            self.files["output"] = self.__config.get("ESCREVA")

        # Run configuration check
        self.__check_config()

        # Initialize parsed input files list
        self.__inputs = []

        # Create base output file
        self.__output = "Word;RecordNumbers"

        # Set '_has_run' variable
        self.__has_run = False
        logging.debug("Inverse list generator instance created")

        # Run query processor
        self.__run()

    def export_output(self) -> None:
        """
        Export output file
        """
        logging.debug("Exporting inverse list output file")
        with open(self.files["output"], mode="w", encoding="utf-8") as file:
            file.write(self.__output)
        logging.debug("Inverse list output file exported")

    def __check_config(self):
        """Check validity of configuration file instructions

        Raises:
            ValueError: In case of invalid configuration file instructions
        """
        if isinstance(self.files["output"], list):
            logging.error(
                "Configuration must have only 1 'ESCREVA' or 'STEMMER' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'ESCREVA' or 'STEMMER' instruction"
            )
        if isinstance(self.files["inputs"], str):
            os.makedirs(os.path.dirname(self.files["inputs"]), exist_ok=True)
        else:
            for file in self.files["inputs"]:
                os.makedirs(os.path.dirname(file), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["output"]), exist_ok=True)

    def __run(self) -> None:
        """
        Run the inverse list generator
        """
        if self.__has_run:
            logging.error("This inverse list generator has already run")
            raise ValueError("This inverse list generator has already run")
        logging.debug("Running InverseList")

        # Parse input files
        if isinstance(self.files["inputs"], str):
            self.__inputs.append(minidom.parse(self.files["inputs"]))
        else:
            for file in self.files["inputs"]:
                self.__inputs.append(minidom.parse(file))

        # Create words dictionary
        words_dict = {}

        # Extract data from inputs
        logging.debug("Extracting data from input(s)")
        for xml in self.__inputs:
            records_dict = FileXML.get_records_data(xml)
            xml_words_dict = ILGTools.create_words_dict(
                records_dict,
                use_steemer = self.__use_stemmer
            )
            for key, value in xml_words_dict.items():
                try:
                    words_dict[key] += value
                except KeyError:
                    words_dict[key] = value

        # Sort dictionary by occurences
        logging.debug("Sorting words dictionary")
        sorted_words_dict = ILGTools.sort_words_dict(words_dict)

        # Save information to output
        logging.debug("Creating output")
        for word, occurences in sorted_words_dict.items():
            self.__output += f"\n{word};{occurences}"

        # Export output file
        logging.debug("Exporting output")
        self.export_output()

        logging.debug("Inverse list generator run finished")
        self.__has_run = True
