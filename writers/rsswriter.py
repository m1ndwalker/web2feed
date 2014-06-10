__author__ = 'Joel Alvim'

import PyRSS2Gen
import datetime
import time
import logging
import re
from email import utils

from xml.sax import saxutils


class RssWriter:

    _records = []
    _filename = ""
    _source_url = ""



    def __init__(self, records, source_url, filename):
        self._records = records
        self._filename = filename
        self._source_url = source_url
        self._logger = logging.getLogger("writers.rsswriter")

    def write(self):

        rss_records = []
        if len(self._records) > 0:
            for record in self._records:
                rss_item = PyRSS2Gen.RSSItem(
                    title= self.unicode_to_valid_xml(record.title),
                    link= self.unicode_to_valid_xml(record.link),
                    description= self.unicode_to_valid_xml(record.description),
                    guid= PyRSS2Gen.Guid(self.unicode_to_valid_xml(record.id), isPermaLink= False),
                    pubDate= self.unicode_to_valid_xml(utils.formatdate(time.mktime(record.date.timetuple()), True))
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


    def unicode_to_valid_xml(self, p_string):
        # When you put utf-8 encoded strings in a XML document you should remember that not all utf-8 valid chars
        # are accepted in a XML document http://www.w3.org/TR/REC-xml/#charsets

        pattern = re.compile("[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD]+")
        valid_xml_string = pattern.sub("",p_string)

        return valid_xml_string