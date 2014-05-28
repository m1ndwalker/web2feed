__author__ = 'Joel Alvim'

import logging
import abc
from abc import ABCMeta


class CrawlerBase(metaclass=ABCMeta):

    _logger = logging.getLogger("crawlers.crawler")

    news_records = []

    @abc.abstractmethod
    def get_url_for_page(self, p_page):
        return ""

    @abc.abstractmethod
    def process_page(self, p_soup, p_last_id):
        return True

    @abc.abstractmethod
    def fetch_body_for(self, p_record, p_record_soup):
        return ""

    def reject_record(self, p_record, p_record_soup):
        return False