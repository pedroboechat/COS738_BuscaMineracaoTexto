"""
Implementation of the search engine
"""

import logging
import os

import pandas as pd
from pandas.core.frame import DataFrame, Series
from tqdm import tqdm

from modules.utils import TFIDF, ConfigParser, Tools, ILGTools, IndexTools

with open("STOPWORDS.txt", encoding="utf-8") as f:
    STOPWORDS = f.read().splitlines()

class SearchEngine():
    """
    Implements a search engine
    """

    def __init__(self) -> None:
        # Get configuration file instructions
        self.__config = ConfigParser("./cfg/BUSCA.CFG").params()

        # Add use_stemmer propriety
        self.__use_stemmer = not self.__config.get("STEMMER") is None

        # Dictionary of file paths
        self.files = {
            "model": self.__config.get("MODELO"),
            "queries": self.__config.get("CONSULTAS")
        }
        if self.__use_stemmer:
            self.files["results"] = self.__config.get("STEMMER")
        else:
            self.files["results"] = self.__config.get("RESULTADOS")

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
            sep = ";",
            dtype = {
                "QueryNumber": int
            }
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
                "Configuration must have only 1 'RESULTADOS' or 'STEMMER' instruction"
            )
            raise ValueError(
                "Configuration must have only 1 'RESULTADOS' or 'STEMMER' instruction"
            )
        os.makedirs(os.path.dirname(self.files["model"]), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["queries"]), exist_ok=True)
        os.makedirs(os.path.dirname(self.files["results"]), exist_ok=True)

    def search(self, query: str, query_index: DataFrame) -> Series:
        """Searches for a query with the model

        Args:
            query (str): Query string to search with
            query_index (DataFrame): Query index for a query to search

        Returns:
            Series: Query search results
        """
        # logging.info(query_index)
        sanitized_query = Tools.sanitize(
            query,
            remove_stopwords = True,
            use_stemmer = self.__use_stemmer
        )
        # breakpoint()
        score = pd.Series(dtype=float)
        # for word in sanitized_query.split():
        #     term = self.__model.loc[
        #         self.__model["Term"] == word
        #     ]
        #     try:
        #         score = score.add(
        #             term.iloc[0, 1:],
        #             fill_value = 0
        #         )
        tf_idf_similarity = TFIDF.get_similarity_tf_idf(
            self.__model,
            sanitized_query,
            query_index
        )
        
        # logging.info(score.loc[score > 0].sort_values(ascending = False))
        # raise Exception()
        return score.loc[score > 0].sort_values(ascending = False)

    def __run(self) -> None:
        """
        Run the search engine
        """
        if self.__has_run:
            logging.error("This search engine has already run")
            raise ValueError("This search engine has already run")
        if self.__use_stemmer:
            logging.debug("Running SearchEngine with Porter Stemmer")
        else:
            logging.debug("Running SearchEngine")

        # Create queries index
        logging.debug("Creating queries records dict")
        queries_records_dict = {}
        for query_number, query_text in self.__queries.itertuples(False, None):
            queries_records_dict[query_number] = query_text

        logging.debug("Creating queries words dict")
        queries_words_dict = ILGTools.create_words_dict(
            queries_records_dict,
            use_steemer = self.__use_stemmer
        )
        logging.debug("Creating queries sorted words dict")
        queries_sorted_words_dict = pd.DataFrame(
            ILGTools.sort_words_dict(queries_words_dict).items(),
            columns = [
                "Word",
                "RecordNumbers"
            ]
        )

        logging.debug("Creating queries Term x Document matrix")
        queries_index = IndexTools.create_term_document_matrix(
            queries_sorted_words_dict,
            "RecordNumbers"
        )
        # with open("test.txt", mode="w") as f:
        #     f.write(str(queries_index))
        # queries_index.to_csv("test.txt")
        # raise

        # Search the input queries
        logging.debug("Starting searches")
        for query_number, query_text in tqdm(
            self.__queries.itertuples(False, None),
            total=self.__queries.shape[0]
        ):
            sanitized_query = Tools.sanitize(
                query_text,
                remove_stopwords = True,
                use_stemmer = self.__use_stemmer
            ).split()
            # breakpoint()

            query_results = pd.DataFrame()
            for doc_number in self.__model.columns[1:]:
                doc_similarity = TFIDF.get_document_similarity_tf_idf(
                    self.__model,
                    queries_index[["Term", query_number]],
                    doc_number,
                    sanitized_query
                )
                query_results = pd.concat(
                    [
                        query_results,
                        pd.DataFrame(
                            [(
                                doc_number,
                                doc_similarity
                            )]
                        )
                    ],
                    ignore_index = True
                )

            self.__results = pd.concat([
                self.__results,
                pd.DataFrame(
                    [(
                        query_number,
                        list(
                            query_results.loc[
                                query_results[1] > 0
                            ].sort_values(
                                by=1,
                                ascending=False
                            ).head(40).reset_index().itertuples(name=None)
                        )
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
