"""
General utility functions
"""

import logging
import re
from typing import Union
from xml.dom.minidom import Element

from unidecode import unidecode


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
                    if key not in self._data.keys():
                        self._data[key] = value
                    else:
                        if isinstance(self._data[key], list):
                            self._data[key].append(value)
                        else:
                            self._data[key] = [self._data[key], key]
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


class XML():
    """
    General XML helper methods
    """
    @staticmethod
    def get_text(nodelist: list) -> str:
        """Return text from a node list

        Args:
            nodelist (list): List of nodes

        Returns:
            str: Extracted text
        """
        partials = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                partials.append(node.data)
        return "".join(partials)


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
        text = XML.get_text(
            element.getElementsByTagName(
                "QueryText"
            )[0].childNodes
        )
        return re.sub(
            r"\s\s+",
            " ",
            unidecode(text.upper())
        ).strip()

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
