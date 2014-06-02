import logging
from urllib.error import URLError
import urllib.request
import time

__author__ = 'Joel Alvim'


class URLConnector:

    _no_attempts = 5
    _no_secs_wait_attempts = 300


    def __init__(self, request):
        self._request = request
        self._logger = logging.getLogger("connectors.urlconnector")

    def connect(self):

        request_f = None

        connection_tries = 0

        while request_f is None and connection_tries < self._no_attempts:
            try:
                request_f = urllib.request.urlopen(self._request)
            except URLError as err:
                self._logger.error("An error occurred requesting %s " % self._request.get_full_url())
                self._logger.error("Waiting %i seconds for next attempt..." % self._no_secs_wait_attempts)

                connection_tries += 1

                time.sleep(self._no_secs_wait_attempts)

        if request_f is None:
            self._logger.error("Couldn't connect to URL %s in under %i attempts. Giving up..." %
                               (self._request.get_full_url(), self._no_attempts))
            raise Exception("Can't connect to %s" % self._request.get_full_url())

        return request_f
