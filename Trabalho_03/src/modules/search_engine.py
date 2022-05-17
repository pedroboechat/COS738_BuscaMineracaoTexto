"""
Implementation of the search engine
"""

import logging
import os

import pandas as pd

from modules.utils import ConfigParser, Tools

with open("STOPWORDS.txt", encoding="utf-8") as f:
    STOPWORDS = f.read().splitlines()

class SearchEngine():
    """
    Implements a search engine
    """

    def __init__(self) -> None:
        # Get configuration file instructions
        self.__config = ConfigParser("./cfg/BUSCA.CFG").params()

        # Dictionary of file paths
        self.files = {
            "model": self.__config.get("MODELO"),
            "queries": self.__config.get("CONSULTAS"),
            "results": self.__config.get("RESULTADOS")
        }

        # Run configuration check
        self.__check_config()

        # Load model
        self.__model = pd.read_csv(
            self.files["model"],
            sep = ";"
        )

        # Load processed queries
        self.__queries = pd.read_csv(
            self.files["queries"],
            sep = ";"
        )

        # Create base results file
        self.__results = pd.DataFrame(
            columns = [
                "SearchNumber",
                "Results"
            ]
        )

        # Set '_has_run' variable
        self.__has_run = False
        logging.debug("SearchEngine instance created")

        # Run search engine
        self.__run()

    def export_output(self) -> None:
        """
        Export output file
        """
        logging.debug("Exporting search engine results file")
        self.__results.to_csv(self.files["results"], sep=";", index=False)
        logging.debug("Search engine results file exported")

    def __check_config(self):
        """Check validity of configuration file instructions

        Raises:
            ValueError: In case of invalid configuration file instructions
        """
        if isinstance(self.files["model"], list):
            logging.error(
                "Configuration must have only 1 'MODELO' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'MODELO' instruction"
            )
        if isinstance(self.files["queries"], list):
            logging.error(
                "Configuration must have only 1 'CONSULTA' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'CONSULTA' instruction"
            )
        if isinstance(self.files["results"], list):
            logging.error(
                "Configuration must have only 1 'RESULTADOS' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'RESULTADOS' instruction"
            )
        os.makedirs(os.path.dirname(self.files["model"]), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["queries"]), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["results"]), exist_ok=True)

    def search(self, query: str) -> pd.Series:
        """Searches for a query with the model

        Args:
            query (str): Query string to search with

        Returns:
            Series: Query search results
        """
        sanitized_query = Tools.sanitize(query, True)
        score = pd.Series()
        for word in sanitized_query.split():
            term = self.__model.loc[
                self.__model["Term"] == word
            ]
            try:
                score = score.add(
                    term.iloc[0, 1:],
                    fill_value = 0
                )
            except IndexError:
                continue
        return score.loc[score > 0].sort_values(ascending = False)

    def __run(self) -> None:
        """
        Run the search engine
        """
        if self.__has_run:
            logging.error("This search engine has already run")
            raise ValueError("This search engine has already run")
        logging.debug("Running SearchEngine")

        # Search the input queries
        logging.debug("Starting searches")
        for query_number, query_text in self.__queries.itertuples(False, None):
            search_results = self.search(query_text)
            result_tuples = []
            rank = 0
            for doc, score in search_results.iteritems():
                rank += 1
                result_tuples.append((rank, int(doc), score))
            self.__results = pd.concat([
                self.__results,
                pd.DataFrame(
                    [(
                        query_number,
                        result_tuples
                    )],
                    columns = [
                        "SearchNumber",
                        "Results"
                    ]
                )
            ])
        logging.debug("Finished searches")

        # Export output file
        logging.debug("Exporting output")
        self.export_output()

        logging.debug("SearchEngine run finished")
        self.__has_run = True
