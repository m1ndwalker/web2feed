__author__ = 'Joel Alvim'

import re
import newsrecord
import urllib

from datetime import datetime


class Crawler:
    base_url = "http://www.gitaarmarkt.nl/"
    search_page_url = "http://www.gitaarmarkt.nl/index.php"
    plugin_name = "gitaarmarkt"

    news_records = []

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

                                        now_date = datetime.today()
                                        publish_date = datetime(year= now_date.year, month= month, day= day)

                                        record.date = publish_date
                                    else:
                                        print("Could not parse date from %s, so just assume now()" % all_text)
                                        record.date = datetime.utcnow()

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

