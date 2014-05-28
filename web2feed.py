__author__ = 'Joel Alvim'

from newsrecord import NewsRecord
from writers.htmlwriter import HtmlWriter
from writers.rsswriter import RssWriter
from resources import resourcemanager

import time
import sys
import getopt
import sqlite3
import os.path
import datetime
import urllib
import random
import logging
import logging.config
import importlib

from bs4 import BeautifulSoup


class Web2Feed:

    def __init__(self, crawlers, max_fetch_pages):
        self._crawlers = crawlers
        self._max_fetch_pages = max_fetch_pages


    # Check if our table exists and if not, create it
    def prep_database(self):

        # Check the path for our database
        db_path = resourcemanager.get_database_path()

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        cur.execute("select name from sqlite_master where type='table' and name='records'")
        if len(cur.fetchall()) < 1:
            cur.execute("CREATE TABLE records "
                        "(id text, link text, title text, description text, date real,"
                        " creation_date real, crawler text)")
            cur.execute("CREATE TABLE crawler_state(last_id text, crawler text unique)")

        return conn, cur

    def crawl(self):

        for crawler in crawlers:

            self._logger.info("---------- Preparing to Crawl with %s" % crawler.plugin_name)

            conn, cur = self.prep_database()

            execution_time_str = (time.strftime("%Y%m%d-%H%M%S"))

            current_fetch_page = 1
            last_id_found = False
            last_id = None

            cur.execute("select last_id from crawler_state where crawler=?", (crawler.plugin_name,))
            last_id_row = cur.fetchone()
            if last_id_row is None:
                self._logger.info("Last Stored News ID for Crawler %s doesn't exist" % crawler.plugin_name)
            else:
                last_id = last_id_row[0]
                self._logger.info("Last Stored News ID for Crawler %s is %s" % (crawler.plugin_name, last_id))


            # Initialize the Random Seed, to be used throughout
            random.random()

            while last_id_found is not True and current_fetch_page <= self._max_fetch_pages:

                req = urllib.request.Request(crawler.get_url_for_page(current_fetch_page),
                                             headers={"User-Agent" : REQUEST_USER_AGENT_STRING})
                f = urllib.request.urlopen(req)
                #f = open("gitaarmarkt.htm", mode="r", encoding="utf-8")

                soup = BeautifulSoup(f,"html5lib")

                self._logger.info("Requesting crawler to process page %i" % current_fetch_page)

                last_id_found = crawler.process_page(soup, last_id)

                f.close()

                # Retrieve the current records and save them to our database, then clean the array
                # We want to be memory efficient

                records = crawler.news_records

                if len(records) == 0:
                    self._logger.info("No new search results found... ")
                else:
                    self._logger.info("Found %s new records" % len(records))

                    # Proceed to fetch the body of each record
                    for rec in records:

                        # To avoid hitting the server always at the same interval, generate a random sleep time in secs
                        sleep_time = random.randint(1,10)
                        self._logger.info("In %i seconds, Fetching body for %s" % (sleep_time, rec.link))

                        time.sleep(sleep_time)

                        record_req = urllib.request.Request(rec.link,
                                                            headers={"User-Agent" : REQUEST_USER_AGENT_STRING})
                        record_f = urllib.request.urlopen(record_req)

                        record_soup = BeautifulSoup(record_f,"html5lib")

                        if not crawler.reject_record(rec, record_soup):
                            body_text = crawler.fetch_body_for(rec, record_soup)
                            if not body_text is None and not body_text == "":
                                rec.description = body_text


                    for rec in records:
                        self._logger.info("Inserting new record with ID: %s" % rec.id)
                        cur.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",
                                    (rec.id,
                                     rec.link,
                                     rec.title,
                                     rec.description,
                                     time.mktime(rec.date.timetuple()),
                                     time.time(),
                                     crawler.plugin_name))

                    # We iterate the pages from most recent to oldest, therefore our last found ID will be the
                    # First item found, on the 1st page.
                    if current_fetch_page == 1:
                        self._logger.info("Saving Last Found ID: %s" % records[len(records) - 1].id)

                        cur.execute("INSERT OR REPLACE into crawler_state(last_id, crawler) values (?,?)",
                                    (records[len(records) - 1].id,crawler.plugin_name))

                    # Clear the crawler list
                    del crawler.news_records[:]

                if last_id_found:
                    self._logger.info("Last Stored News ID Found: " + last_id)
                    break

                self._logger.info("Processed page %s" % current_fetch_page)

                sleep_time = random.randint(10,20)
                # Wait 10-20 seconds before requesting the next page. We don't want to overload the server and get banned
                # Don't always use the same period to appear more human
                if current_fetch_page < self._max_fetch_pages:
                    self._logger.info("Waiting %i seconds for next page..." % sleep_time)
                    time.sleep(sleep_time)

                current_fetch_page += 1

            # Commit results immediately after having fetched them all (there can be an error thrown
            # in the output generation part and then nothing is saved to the database)
            conn.commit()

            if writer == "htmlwriter":
                results_file_name = os.path.normpath(out_path + "/" + crawler.plugin_name + "_results_" + execution_time_str +  ".htm")

                new_records = []
                for row in cur.execute(
                        "SELECT id, link, title, description, datetime(date, 'unixepoch', 'localtime'), "
                        "datetime(creation_date, 'unixepoch', 'localtime'), crawler "
                        "from records where crawler=? and datetime(creation_date,'unixepoch') >= "
                        "datetime('now',?) order by creation_date desc, id asc",
                        (crawler.plugin_name, write_items_since)):

                    record = NewsRecord()
                    record.id = row[0]
                    record.link = row[1]
                    record.title = row[2]
                    record.description= row[3]
                    record.date = datetime.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
                    record.creation_date = datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                    record.crawler_name = row[6]

                    new_records.append(record)

                if len(new_records) > 0:

                    html_writer = HtmlWriter(new_records, results_file_name)
                    html_writer.write()

                    self._logger.info("Writing HTML file to %s" % results_file_name)
                else:
                    self._logger.info("No records found created in the past %s. Not generating HTML file"
                                      % write_items_since)

            elif writer == "rsswriter":
                results_file_name = os.path.normpath(out_path + "/" + crawler.plugin_name + ".xml")

                # Get the records inserted i
                rss_records = []
                for row in cur.execute(
                        "SELECT id, link, title, description, datetime(date, 'unixepoch', 'localtime'), "
                        "datetime(creation_date, 'unixepoch', 'localtime'), crawler "
                        "from records where crawler=? and datetime(creation_date,'unixepoch') >= "
                        "datetime('now',?) order by creation_date desc, id asc",
                        (crawler.plugin_name, write_items_since)):

                    #print(row)


                    record = NewsRecord()
                    record.id = row[0]
                    record.link = row[1]
                    record.title = row[2]
                    record.description= row[3]
                    record.date = datetime.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
                    record.creation_date = datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                    record.crawler_name = row[6]

                    rss_records.append(record)

                if len(rss_records) > 0:
                    rss_writer = RssWriter(rss_records, crawler.base_url, results_file_name)
                    rss_writer.write()

                    self._logger.info("Writing RSS file to %s" % results_file_name)
                else:
                    self._logger.info("No records found created in the past %s. Not generating RSS file"
                                      % write_items_since)

            conn.close()

            self._logger.info("---------- Finished Crawling with %s" % crawler.plugin_name)

#Max Fetch pages Default value is 5
max_fetch_pages = 5
#Writer Default is html
writer = "htmlwriter"
#Default path is the current directory
out_path = os.path.normpath("./")
#Default Generate Output file with items created in the past x minutes
write_items_since="-360 minutes"

# List containing the Instantiated Crawlers to crawl with
crawlers = []

REQUEST_USER_AGENT_STRING = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ " \
                            "(KHTML, like Gecko) Version/5.1.7 Safari/534.57.2"

# Check Shell Params
try:
    if len(sys.argv) <= 1:
        raise getopt.GetoptError("Not enough arguments")

    opts, args = getopt.getopt(sys.argv[1:], "", ["crawlers=", "max-fetch-p=", "writer=", "out-path=", "write_items_since="])
except getopt.GetoptError:
    print("Usage: web2feed.py --crawler=crawler_to_use --max-fetch-p=max_number_pages_to_fetch "
          "--writer=writer_to_use --write_items_since=time_in_minutes --out-path=output_path_for_writer")
    sys.exit(2)
for opt, arg in opts:
    if opt == "--crawlers":

        crawlers_arg = arg.split(",")

        try:

            for crawler_arg in crawlers_arg:

                # The code below checks the package named after the crawler is passed in as an argument
                # and attempts to instantiate the expected class Crawler therein

                crawler_plugin = importlib.import_module("crawlers." + crawler_arg)
                crawler_construct = getattr(crawler_plugin, "Crawler")
                crawler = crawler_construct()

                crawlers.append(crawler)

        except ImportError as err:
            print("Error loading module: {0}".format(err))
            exit(1)

    elif opt == "--max-fetch-p":
        max_fetch_pages = arg

    elif opt == "--writer":
        if arg not in ["htmlwriter","rsswriter"]:
            print("Specified writer %s doesn't exist" % arg)
            exit(1)

        writer = arg

    elif opt == "--write_items_since":
        write_items_since = "-%s minutes" % arg

    elif opt == "--out-path":
        out_path = os.path.normpath(arg)
        out_path = os.path.expanduser(out_path)

        if not os.path.exists(out_path):
            print("Specified output path %s doesn't exist" % arg)
            exit(1)

# Set default Logging level to INFO
logging.basicConfig(level=logging.INFO)

# Check if we have a logging configuration file in the current working directory and if so, use it
curr_dir = os.path.realpath('./')
logging_conf_f = os.path.join(curr_dir, "logging.conf")
if os.path.isfile(logging_conf_f):
    print("Logging configuration file found in %s" % logging_conf_f)
    logging.config.fileConfig(logging_conf_f)
else:
    print("No logging.conf file has been found in %s" % curr_dir)

# Get the logger for this class
logger = logging.getLogger("web2feed")

logger.info("Configured crawlers: %s" % crawlers)
logger.info("Max Pages to Fetch: %s" % max_fetch_pages)
logger.info("Writer to use: %s" % writer )
logger.info("Write records created since number of minutes in the past: %s" % write_items_since )
logger.info("Output Path: %s" % out_path )

news_crawler = Web2Feed(crawlers, int(max_fetch_pages))
news_crawler._logger =  logger
news_crawler.crawl()