"""
General utility functions
"""

import logging
import re
from typing import Union
from xml.dom.minidom import Element, Document

from unidecode import unidecode
import numpy as np


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
    def sanitize(string: str, remove_stopwords: bool = False) -> str:
        """Sanitize a text string

        Args:
            string (str): String to sanitize

        Returns:
            str: Sanitized string
        """
        if remove_stopwords:
            stopwords = Tools.get_stopwords()
            text = re.sub(
                r"[.,;:?!\[\]\-\"'_()%]",
                " ",
                re.sub(
                    r"\s\s+",
                    " ",
                    unidecode(string.replace("\n", " ").upper())
                )
            ).strip().split(" ")
            for stopword in stopwords:
                text = list(filter((stopword).__ne__, text))
            text = list(filter(lambda x: not x.isdigit(), text))
            text = list(filter(lambda x: len(x) > 2, text))
            text = ' '.join(text)
            return re.sub(
                r"\s\s+",
                " ",
                text.strip()
            )

        return re.sub(
            r"[.,;:?!\[\]\-\"'_()%]",
            " ",
            re.sub(
                r"\s\s+",
                " ",
                unidecode(string.replace("\n", " ").upper())
            )
        ).strip()


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
        return 1 + (np.log(frequency) * np.log(total_docs/docs_with_term))
