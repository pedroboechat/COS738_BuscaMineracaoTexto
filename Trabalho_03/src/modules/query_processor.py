"""
Implementation of the query processor
"""

import logging
import os
from xml.dom import minidom

from modules.utils import ConfigParser, FileQueryXML


class QueryProcessor():
    """
    Implements a query processor
    """

    def __init__(self) -> None:
        # Get configuration file instructions
        self._config = ConfigParser("./cfg/PC.CFG").params()

        # Dictionary of file paths
        self.files = {
            "original": self._config.get("LEIA"),
            "processed": self._config.get("CONSULTAS"),
            "expected": self._config.get("ESPERADOS")
        }

        # Run configuration check
        self._check_config()

        # Parse original file
        self._original = minidom.parse(self.files["original"])

        # Create base output files
        self._processed = "QueryNumber;QueryText"
        self._expected = "QueryNumber;DocNumber;DocVotes"

        # Set '_has_run' variable
        self._has_run = False
        logging.debug("Query processor instance created")

        # Run query processor
        self._run()

    def export_processed(self) -> None:
        """
        Export processed queries file
        """
        logging.debug("Exporting processed queries file")
        with open(self.files["processed"], mode="w", encoding="utf-8") as file:
            file.write(self._processed)
        logging.debug("Processed queries file exported")

    def export_expected(self) -> None:
        """
        Export expected results file
        """
        logging.debug("Exporting expected results file")
        with open(self.files["expected"], mode="w", encoding="utf-8") as file:
            file.write(self._expected)
        logging.debug("Expected results file exported")

    def _check_config(self):
        """Check validity of configuration file instructions

        Raises:
            ValueError: In case of invalid configuration file instructions
        """
        if isinstance(self.files["original"], list):
            logging.error(
                "Configuration must have only 1 'LEIA' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'LEIA' instruction"
            )
        if isinstance(self.files["processed"], list):
            logging.error(
                "Configuration must have only 1 'CONSULTAS' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'CONSULTAS' instruction"
            )
        if isinstance(self.files["expected"], list):
            logging.error(
                "Configuration must have only 1 'ESPERADOS' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'ESPERADOS' instruction"
            )
        for file in self.files.values():
            os.makedirs(os.path.dirname(file), exist_ok=True)

    def _run(self) -> None:
        """
        Run the query processor
        """
        if self._has_run:
            logging.error("This query processor has already run")
            raise ValueError("This query processor has already run")
        logging.debug("Running QueryProcessor")

        # Get 'QUERY' element
        queries = self._original.getElementsByTagName("QUERY")

        # Extract data from original file and create outputs
        logging.debug("Extracting original FileQueryXML and creating outputs")
        for query in queries:
            query_number = FileQueryXML.get_query_number(query)
            query_text = FileQueryXML.get_query_text(query)
            query_results = FileQueryXML.get_query_results(query)
            self._processed += f"\n{query_number};{query_text}"
            for item, score in query_results.items():
                votes = sum([int(i) > 0 for i in score])
                self._expected += f"\n{query_number};{item};{votes}"

        # Run exporters
        self.export_processed()
        self.export_expected()

        # End run
        logging.debug("Query processor run finished")
        self._has_run = True
