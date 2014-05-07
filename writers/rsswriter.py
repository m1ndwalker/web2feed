__author__ = 'Joel Alvim'

import PyRSS2Gen
import datetime
import time
from email import utils


class RssWriter:

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
                    author= __author__,
                    title= record.title,
                    link= record.link,
                    description= record.title + " - " + record.description,
                    guid= record.id,
                    pubDate= utils.formatdate(time.mktime(record.date.timetuple()))
                )

                rss_records.append(rss_item)

            rss = PyRSS2Gen.RSS2(
                title="RSS Dump for NewsCrawler " + self._records[0].crawler_name,
                link= self._source_url,
                description="RSS Dump from selected sources",

                lastBuildDate= utils.formatdate(time.mktime(datetime.datetime.now().timetuple())),
                items=rss_records
            )

            print("Attempting to Save Records into file: %s" % self._filename)

            write_f = open(self._filename, encoding="utf-8", mode="w")
            rss.write_xml(write_f, "utf-8")


