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

from bs4 import BeautifulSoup


class Web2Feed:

    def __init__(self, crawler, max_fetch_pages):
        self._crawler = crawler
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

        conn, cur = self.prep_database()

        execution_time_str = (time.strftime("%Y%m%d-%H%M%S"))

        current_fetch_page = 1
        last_id_found = False
        last_id = None

        cur.execute("select last_id from crawler_state where crawler=?", (self._crawler.plugin_name,))
        last_id_row = cur.fetchone()
        if last_id_row is None:
            print("Last Stored News ID for Crawler %s doesn't exist" % self._crawler.plugin_name)
        else:
            last_id = last_id_row[0]
            print("Last Stored News ID for Crawler %s is %s" % (self._crawler.plugin_name, last_id))


        # Initialize the Random Seed, to be used throughout
        random.random()

        while last_id_found is not True and current_fetch_page <= self._max_fetch_pages:

            req = urllib.request.Request(self._crawler.get_url_for_page(current_fetch_page),
                                         headers={"User-Agent" : REQUEST_USER_AGENT_STRING})
            f = urllib.request.urlopen(req)
            #f = open("gitaarmarkt.htm", mode="r", encoding="utf-8")

            soup = BeautifulSoup(f,"html5lib")

            print("Requesting crawler to process page %i" % current_fetch_page)

            last_id_found = self._crawler.process_page(soup, last_id)

            f.close()

            # Retrieve the current records and save them to our database, then clean the array
            # We want to be memory efficient

            records = self._crawler.news_records

            if len(records) == 0:
                print("No new search results found... ")
            else:
                print("Found %s new records" % len(records))

                # Proceed to fetch the body of each record
                for rec in records:

                    # To avoid hitting the server always at the same interval, generate a random sleep time in secs
                    sleep_time = random.randint(1,10)
                    print("In %i seconds, Fetching body for %s" % (sleep_time, rec.link))

                    time.sleep(sleep_time)

                    record_req = urllib.request.Request(rec.link,
                                                        headers={"User-Agent" : REQUEST_USER_AGENT_STRING})
                    record_f = urllib.request.urlopen(record_req)

                    record_soup = BeautifulSoup(record_f,"html5lib")
                    body_text = self._crawler.fetch_body_for(rec, record_soup)

                    if not body_text is None and not body_text == "":
                        rec.description = body_text


                for rec in records:
                    print("Inserting new record with ID: %s" % rec.id)
                    cur.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",
                                (rec.id,
                                 rec.link,
                                 rec.title,
                                 rec.description,
                                 time.mktime(rec.date.timetuple()),
                                 time.time(),
                                 self._crawler.plugin_name))

                # We iterate the pages from most recent to oldest, therefore our last found ID will be the
                # First item found, on the 1st page.
                if current_fetch_page == 1:
                    print("Saving Last Found ID: %s" % records[len(records) - 1].id)

                    cur.execute("INSERT OR REPLACE into crawler_state(last_id, crawler) values (?,?)",
                                (records[len(records) - 1].id,self._crawler.plugin_name))

                # Clear the crawler list
                del self._crawler.news_records[:]

            if last_id_found:
                print("Last Stored News ID Found: " + last_id)
                break

            print("Processed page %s" % current_fetch_page)

            sleep_time = random.randint(10,20)
            # Wait 10-20 seconds before requesting the next page. We don't want to overload the server and get banned
            # Don't always use the same period to appear more human
            if current_fetch_page < self._max_fetch_pages:
                print("Waiting %i seconds for next page..." % sleep_time)
                time.sleep(sleep_time)

            current_fetch_page += 1

        # Commit results immediately after having fetched them all (there can be an error thrown
        # in the output generation part and then nothing is saved to the database)
        conn.commit()

        if writer == "htmlwriter":
            results_file_name = os.path.normpath(out_path + "/" + self._crawler.plugin_name + "_results_" + execution_time_str +  ".htm")

            if not last_id is None:
                cur.execute("select rowid from records where id=?", (last_id,))

                last_id_rowid = cur.fetchone()[0]
                cur.execute("SELECT id, link, title, description, datetime(date, 'unixepoch', 'localtime'), "
                            "datetime(creation_date, 'unixepoch', 'localtime'), crawler "
                            "from records where rowid > ?", (last_id_rowid,))
            else:
                cur.execute("SELECT id, link, title, description, datetime(date, 'unixepoch', 'localtime'), "
                            "datetime(creation_date, 'unixepoch', 'localtime'), crawler "
                            "from records")

            new_records = []
            for row in cur:

                record = NewsRecord()
                record.id = row[0]
                record.link = row[1]
                record.title = row[2]
                record.description= row[3]
                record.date = datetime.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
                record.creation_date = datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                record.crawler_name = row[6]

                new_records.append(record)

            html_writer = HtmlWriter(new_records, results_file_name)
            html_writer.write()

        elif writer == "rsswriter":
            results_file_name = os.path.normpath(out_path + "/" + self._crawler.plugin_name + ".xml")

            # Get the last 200 records
            rss_records = []
            for row in cur.execute(
                    "SELECT id, link, title, description, datetime(date, 'unixepoch', 'localtime'), "
                    "datetime(creation_date, 'unixepoch', 'localtime'), crawler "
                    "from records where crawler=? order by creation_date desc, id asc limit 200",
                    (self._crawler.plugin_name,)):

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

            rss_writer = RssWriter(rss_records, self._crawler.base_url, results_file_name)
            rss_writer.write()

        conn.close()

#Max Fetch pages Default value is 5
max_fetch_pages = 5
#Writer Default is html
writer = "htmlwriter"
#Default path is the current directory
out_path = os.path.normpath("./")

REQUEST_USER_AGENT_STRING = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ " \
                            "(KHTML, like Gecko) Version/5.1.7 Safari/534.57.2"

# Check Shell Params
try:
    if len(sys.argv) <= 1:
        raise getopt.GetoptError("Not enough arguments")

    opts, args = getopt.getopt(sys.argv[1:], "", ["crawler=", "max-fetch-p=", "writer=", "out-path="])
except getopt.GetoptError:
    print("Usage: web2feed.py --crawler=crawler_to_use --max-fetch-p=max_number_pages_to_fetch "
          "--writer=writer_to_use --out-path=output_path_for_writer")
    sys.exit(2)
for opt, arg in opts:
    if opt == "--crawler":
        try:
            # The code below checks the package named after the crawler passed in as an argument
            # and attempts to instantiate the expected class Crawler therein

            crawler_plugin = __import__("crawlers." + arg, fromlist=["Crawler"])
            crawler_construct = getattr(crawler_plugin, "Crawler")
            crawler = crawler_construct()
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

    elif opt == "--out-path":
        out_path = os.path.normpath(arg)
        out_path = os.path.expanduser(out_path)

        if not os.path.exists(out_path):
            print("Specified output path %s doesn't exist" % arg)
            exit(1)

print("Configured crawler: %s" % crawler.plugin_name )
print("Max Pages to Fetch: %s" % max_fetch_pages )
print("Writer to use: %s" % writer )
print("Output Path: %s" % out_path )

news_crawler = Web2Feed(crawler, int(max_fetch_pages))
news_crawler.crawl()