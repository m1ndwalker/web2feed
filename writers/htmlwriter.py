__author__ = 'Joel Alvim'

import logging

class HtmlWriter:

    _records = []
    _filename = ""

    def __init__(self, records, filename):
        self._records = records
        self._filename = filename
        self._logger = logging.getLogger("writers.htmlwriter")

    def write(self):

        if not len(self._records) > 0:
            self._logger.info("No new Records to write with HtmlWriter")
            return

        self._logger.info("Attempting to Save Records into file: %s" % self._filename)

        write_f_dump = open(self._filename, encoding="utf-8", mode="w")

        write_f_dump.writelines(
            ['<!DOCTYPE HTML>\n',
             '<html>\n',
             ' <head>\n',
             " <meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">\n",
            ' <title>Dump</title>\n',
           ' <body>\n'])

        for rec in self._records:
            write_f_dump.writelines(
            [' ID: ' + rec.id + '<br>\n',
             ' Title: ' + rec.title + '<br>\n',
             ' Published Date: ' + rec.date.strftime("%Y-%m-%d %H:%M:%S") + '<br>\n',
             ' Creation Date: ' + rec.creation_date.strftime("%Y-%m-%d %H:%M:%S") + '<br>\n',
             ' Description: ' + rec.description + '<br>\n',
             ' Link: <a href="' + rec.link + '">' + rec.link + '</a><br>\n',
             ' <p>\n'])

        write_f_dump.writelines(
            [' </body>\n',
             '</html>\n'])

        write_f_dump.close()