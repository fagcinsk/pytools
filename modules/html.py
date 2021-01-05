#!/usr/bin/env python
from bs4 import BeautifulSoup
from requests import get


class Html:
    """HTML utilities"""

    def sel(self, url, selector):
        """Shows some part of source by selector

        selector -- css selector, ex.: ul>li
        """
        for res in self._soup(url).select(selector):
            print(res.prettify())

    def xpath(self, url, xpath):
        """Shows some part of source by xpath

        xpath -- ex.: //a/@href
        """
        from lxml import etree
        for res in self._lxml(url).xpath(xpath):
            if isinstance(res, etree._ElementUnicodeResult):
                print(res)
            else:
                print(etree.tostring(res, pretty_print=True).decode())

    def src(self, url):
        """Shows prettified html source,"""
        print(self._soup(url).prettify())

    @staticmethod
    def _soup(url):
        return BeautifulSoup(get(url).text, 'html.parser')

    @staticmethod
    def _lxml(url):
        from lxml import html
        return html.fromstring(get(url).text)
