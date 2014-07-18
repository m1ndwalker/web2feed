__author__ = 'Joel Alvim'

import re
import newsrecord
import urllib
import logging

from datetime import datetime
from crawlers import crawlerbase


class Crawler(crawlerbase.CrawlerBase):

    base_url = "http://www.gitaarmarkt.nl/"
    search_page_url = "http://www.gitaarmarkt.nl/index.php"
    plugin_name = "gitaarmarkt"


    def __init__(self):
        _logger = logging.getLogger("crawlers.gitaarmarkt")


    def get_url_for_page(self, p_page):

        params = urllib.parse.urlencode({
            'ct': '',
            'md': 'browse',
            'page': p_page,
            'mds': 'search',
            'brief_key': '',
            'before': '',
            'type': '',
            'salary': '',
            'goal': ''})

        return self.search_page_url + '?' + params


    def process_page(self, p_soup, p_last_id):

        link = p_soup.find("b",text = re.compile('.*Details.*'))

        # Test first if the link was found. In some circumstances it may not exist (if for instance
        # we've requested a page number that doesn't exist. At the time of writing this, the
        # limit on GitaarMarkt is 40

        if link is not None:

            for parent in link.parents:
                # Get the Table element that hosts the Data view
                table_found = False

                if parent.name == "table":
                    table_found = True
                    row_count = 0

                    for table_row in parent.find_all("tr"):

                        row_count += 1
                        column_count = 0

                        # Ignore the first row since it's the header Row
                        if row_count > 1:

                            record = newsrecord.NewsRecord()

                            for table_column in table_row.find_all("td"):
                                column_count += 1

                                # This is the column with the link that we want
                                if column_count == 8:
                                    record.link = self.base_url + table_column.a['href']
                                else:
                                    text_bits = table_column.find_all(text = re.compile('[a-zA-Z0-9]*'))
                                    all_text = ""

                                    for textBit in text_bits:
                                        all_text = all_text + textBit.strip()

                                    # Column containing the Category
                                    if column_count == 1:
                                        record.category = all_text

                                    # Column containing the ID
                                    elif column_count == 2:
                                        if all_text == p_last_id:
                                            return True

                                        record.id = all_text

                                    # Column Containing the Date
                                    elif column_count == 3:

                                        match = re.search("(\d+)-(\d+)", all_text, re.IGNORECASE)
                                        if match:
                                            day = int(match.group(1))
                                            month = int(match.group(2))

                                            curr_time = datetime.today()

                                            publish_date = datetime(year= curr_time.year, month= month, day= day)

                                            record.date = publish_date
                                        else:
                                            self._logger.warning("Could not parse date from %s, so just assume today()" % all_text)
                                            record.date = datetime.today()

                                    # Column Containing the Type
                                    elif column_count == 4:
                                        record.description = record.description + "Type: " + all_text + " / "

                                    # Column Containing the Title
                                    elif column_count == 5:
                                        record.title = all_text

                                    # Column Containing the Price
                                    elif column_count == 6:
                                        record.description = record.description + "Price: " + all_text + " / "

                            self.news_records.insert(0, record)

                if table_found:
                    break

        return False


    def fetch_body_for(self, p_record, p_record_soup):

        # We have to find a <b> attribute that includes the text below
        b_tag = p_record_soup.find("b",text = re.compile('.*Advertentie geplaatst door.*'))

        # Now we need to first the second parent table of the tag, and this is our body
        parent_tables = b_tag.find_parents(name= "table", limit= 1)

        if len(parent_tables) != 1:
            self._logger.error("An error occurred fetching the body for record %s. Can't find second parent table to <b> with the title." % p_record.title)
            return None

        content_soup = parent_tables[0]

        # Further strip down the content to take up less space with things we don't need.
        # Get rid of font tags
        for font in content_soup.find_all('font'):
            font.unwrap();
        # Get rid of spacers
        for font in content_soup.find_all('spacer'):
            font.extract();

        return str(content_soup)

