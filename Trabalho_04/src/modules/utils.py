"""
General utility functions
"""

import logging
import re
from typing import Union
from xml.dom.minidom import Element, Document

from unidecode import unidecode
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame, Series

from modules.porter_stemmer import PorterStemmer


class ConfigParser():
    """
    Parser for the configuration files
    """

    def __init__(self, filename: str) -> None:
        self._filename = filename
        self._data = {}
        self._parse_data()

    @staticmethod
    def _find_none(index) -> Union[int, None]:
        if index == -1:
            return None
        return index - 2

    def _parse_data(self) -> None:
        logging.debug(
            "Starting configuration parsing for '%s'",
            self._filename
        )
        with open(self._filename, encoding="utf-8") as file:
            lines = file.read().splitlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                try:
                    key, value = line.replace(
                        '"',
                        ""
                    )[:self._find_none(line.find("#"))].split("=")
                    logging.debug("%s =  %s", repr(key), repr(value))
                    if value == "":
                        raise ValueError()
                    try:
                        if isinstance(self._data[key], list):
                            self._data[key].append(value)
                        else:
                            self._data[key] = [self._data[key], value]
                    except KeyError:
                        self._data[key] = value
                except ValueError:
                    logging.error(
                        "Couldn't extract configuration from '%s'",
                        line
                    )
        logging.debug("Finished parsing '%s'", self._filename)

    def get(self, key: str) -> Union[str, None]:
        """Get a configuration parameter by key

        Args:
            key (str): The parameter to retreive

        Returns:
            Union[str, None]: The value for the parameter. In case of not existing,
            returns None.
        """
        return self._data.get(key)

    def params(self) -> dict:
        """Get full dictionary of parameters

        Returns:
            dict: Parameters of the configuration file
        """
        return self._data


class Tools():
    """
    General tools
    """
    @staticmethod
    def get_stopwords() -> str:
        """Loads stopwords"""
        with open("STOPWORDS.txt", encoding="utf-8") as file:
            stopwords = file.read().splitlines()
        return stopwords

    @staticmethod
    def sanitize(string: str, remove_stopwords: bool = False, use_stemmer: bool = False) -> str:
        """Sanitize a text string

        Args:
            string (str): String to sanitize
            remove_stopwords (bool): Whether to remove stopwords
            use_stemmer (bool): Whether to use the Porter Stemmer

        Returns:
            str: Sanitized string
        """
        if not remove_stopwords and not use_stemmer:
            return re.sub(
                r"[.,;:?!\\\/\+><=\[\]\-\"'_()%]",
                " ",
                re.sub(
                    r"\s\s+",
                    " ",
                    unidecode(string.replace("\n", " ").upper())
                )
            ).strip()

        text = string[:]

        if remove_stopwords:
            stopwords = Tools.get_stopwords()
            text = re.sub(
                r"[.,;:?!\\\/\+><=\[\]\-\"'_()%]",
                " ",
                re.sub(
                    r"\s\s+",
                    " ",
                    unidecode(text.replace("\n", " ").upper())
                )
            ).strip().split(" ")
            for stopword in stopwords:
                text = list(filter((stopword).__ne__, text))
            text = list(filter(lambda x: x.isalpha(), text))
            text = list(filter(lambda x: len(x) > 2, text))
            text = ' '.join(text)
            text = re.sub(
                r"\s\s+",
                " ",
                text.strip()
            )

        if use_stemmer:
            stemmer = PorterStemmer()
            text = " ".join([
                stemmer.stem(word.lower(), 0, len(word)-1).upper()
                for word in text.split()
            ])
        return text


class XML():
    """
    General XML helper methods
    """
    @staticmethod
    def get_text(nodelist: list, extra_sanitizing: bool = False) -> str:
        """Return text from a node list

        Args:
            nodelist (list): List of nodes
            extra_sanitizing (bool): Whether to remove ponctuation
            and other characthers

        Returns:
            str: Extracted text
        """
        partials = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                partials.append(node.data)
        joined = "".join(partials)
        if extra_sanitizing:
            joined = Tools.sanitize(joined)
        return re.sub(
            r"\s\s+",
            " ",
            unidecode(joined.replace("\n", " ").replace(";", " ").upper())
        ).strip()


class FileQueryXML():
    """
    FileQuery XML helper methods
    """
    @staticmethod
    def get_query_number(element: Element) -> str:
        """Get 'QueryNumber' text from a 'Query' element

        Args:
            element (Element): An 'Query' tag element

        Returns:
            str: The query number of the element
        """
        return XML.get_text(
            element.getElementsByTagName(
                "QueryNumber"
            )[0].childNodes
        )

    @staticmethod
    def get_query_text(element: Element) -> str:
        """Get 'QueryText' text from a 'Query' element

        Args:
            element (Element): An 'Query' tag element

        Returns:
            str: The query text of the element
        """
        return XML.get_text(
            element.getElementsByTagName(
                "QueryText"
            )[0].childNodes
        )

    @staticmethod
    def get_query_results(element: Element) -> dict:
        """Get expected results from a 'Query' element

        Args:
            element (Element): An 'Query' tag element

        Returns:
            dict: A dictionary with the result items as keys and
            and its scores as values
        """
        records = element.getElementsByTagName(
            "Records"
        )[0].getElementsByTagName(
            "Item"
        )
        query_result = {}
        for record in records:
            item = XML.get_text(record.childNodes)
            score = dict(record.attributes.items()).get("score")
            query_result[item] = score

        return query_result


class FileXML():
    """
    File XML helper methods
    """
    @staticmethod
    def get_records_data(document: Document) -> dict:
        """Get 'RECORDNUM' and 'ABSTRACT' (or 'EXTRACT') from all
        'RECORD' elements

        Args:
            document (Document): A 'FILE' MiniDOM document

        Returns:
            dict: A dictionary containing records data
        """
        records_dict = {}

        for record in document.getElementsByTagName("RECORD"):
            record_num = int(XML.get_text(
                record.getElementsByTagName(
                    "RECORDNUM"
                )[0].childNodes
            ))
            try:
                abstract = XML.get_text(
                    record.getElementsByTagName(
                        "ABSTRACT"
                    )[0].childNodes,
                    extra_sanitizing = True
                )
            except IndexError:
                try:
                    abstract = XML.get_text(
                        record.getElementsByTagName(
                            "EXTRACT"
                        )[0].childNodes,
                        extra_sanitizing = True
                    )
                except IndexError:
                    continue
            records_dict[record_num] = abstract
        return records_dict

class ILGTools():
    """
    Helper class to Inverse List Generator
    """
    @staticmethod
    def create_words_dict(records_dict: dict, use_steemer: bool = False) -> dict:
        """Creates a words dictionary for a given records dictionary

        Args:
            records_dict (dict): A records dictionary
            use_steemer (bool, optional): Whether to use the steemer. Defaults to False.

        Returns:
            dict: Words dictionary
        """
        words_dict = {}
        for record_num, string in records_dict.items():
            text = Tools.sanitize(string, remove_stopwords = True, use_stemmer = use_steemer)
            for word in text.split():
                if (
                    word.isdigit() or
                    len(word) < 3
                ):
                    continue
                try:
                    words_dict[word].append(record_num)
                except KeyError:
                    words_dict[word] = [record_num]
        return words_dict

    @staticmethod
    def sort_words_dict(words_dict: dict) -> dict:
        """Sorts a words dictionary

        Args:
            words_dict (dict): The words dictionary to be sorted

        Returns:
            dict: The sorted words dictionary
        """
        return {
            item: words_dict[item] for item in sorted(
                words_dict,
                key = lambda x: len(words_dict[x]),
                reverse = True
            )
        }


class IndexTools():
    """
    Helper class to Indexer    
    """
    @staticmethod
    def create_term_document_matrix(dataframe: DataFrame, records_column: str) -> DataFrame:
        """Creates a Term x Document matrix

        Args:
            all_documents (list): All documents list

        Returns:
            DataFrame: Term x Document matrix
        """
        all_documents = set()
        for docs in dataframe[records_column]:
            for doc in docs:
                all_documents.add(doc)
        all_documents = sorted(all_documents)
        total_docs = len(all_documents)

        term_document_matrix = pd.DataFrame(
            columns = ["Term"] + all_documents
        )

        term_count = {
            i: j
            for _, (i, j) in dataframe.iterrows()
        }

        all_rows = []
        for term in term_count.keys():
            row = {}
            row["Term"] = term
            docs_with_term = len(np.unique(term_count[term]))
            for doc in all_documents:
                row[doc] = TFIDF.get_tf_idf(term_count[term].count(doc), total_docs, docs_with_term)
            all_rows.append(row)

        term_document_matrix = pd.concat(
            [term_document_matrix, pd.DataFrame(all_rows)]
        )

        return term_document_matrix


class TFIDF():
    """
    Implements TD-IDF standard
    """
    @staticmethod
    def get_tf_idf(
        frequency: int,
        total_docs: int,
        docs_with_term: int
    ) -> float:
        """Calculates TF-IDF"""
        if frequency == 0:
            return 0
        return (1 + np.log(frequency)) * np.log(total_docs/docs_with_term)

    @staticmethod
    def get_document_similarity_tf_idf(
        model: DataFrame,
        query_index: DataFrame,
        doc_number: int,
        sanitized_query: list
    ) -> float:
        """Gets similarity of two TD-IDF lists

        Args:
            documents_tf_idf (Series): A Series of TF-IDFs of a term for each document
            query_tf_idf (float): The TF-IDF of the same term on a query

        Returns:
            float: Calculated similarity
        """

        scalar_prod = 0
        length_q = 0
        length_w = 0

        for term in sanitized_query:
            try:
                query_w = query_index.loc[
                    query_index["Term"] == term
                ].iloc[0, 1]
                
                doc_w = model.loc[
                    model["Term"] == term
                ][str(doc_number)].iloc[0]
            except:
                print(doc_number, term)
                continue

            scalar_prod += query_w * doc_w
            length_q += query_w**2
            length_w += doc_w**2

        length = np.sqrt(length_q) * np.sqrt(length_w)
        # if int(doc_number) == 139:
        #     breakpoint()
        if length > 0:
            return scalar_prod/length
        return 0
