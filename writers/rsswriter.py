__author__ = 'Joel Alvim'

import PyRSS2Gen
import datetime
import time
import logging
from email import utils

from xml.sax import saxutils


class RssWriter:

    _logger = logging.getLogger("writers.rsswriter")

    _records = []
    _filename = ""
    _source_url = ""

    def __init__(self, records, source_url, filename):
        self._records = records
        self._filename = filename
        self._source_url = source_url

    def write(self):

        rss_records = []
        if len(self._records) > 0:
            for record in self._records:
                rss_item = PyRSS2Gen.RSSItem(
                    author= "1llum1nat1",
                    title= record.title,
                    link= record.link,
                    description= record.description,
                    guid= record.id,
                    pubDate= utils.formatdate(time.mktime(record.date.timetuple()), True)
                )

                rss_records.append(rss_item)

            rss = PyRSS2Gen.RSS2(
                title="RSS Dump for NewsCrawler " + self._records[0].crawler_name,
                link= self._source_url,
                description="RSS Dump from selected sources",

                lastBuildDate= utils.formatdate(time.mktime(datetime.datetime.now().timetuple()), True),
                items=rss_records
            )

            # Write to a string first, since PyRSS2Gen uses internally the escape method of saxutils.py

            #rss_text = rss.to_xml(encoding="utf-8")

            # Now use Beautiful Soup to fix the character escapes inside CDATA structures

            #rss_text = saxutils.unescape(rss_text)

            self._logger.info("Attempting to Save Records into file: %s" % self._filename)

            write_f = open(self._filename, encoding="utf-8", mode="w")
            rss.write_xml(write_f, "utf-8")

            #write_f.write(rss_text)



