__author__ = 'Joel Alvim'


class NewsRecord:
    id = ""
    # date is supposed to be the publishing date, a datetime object
    date = None
    title = ""
    description = ""
    category = ""
    link = ""
    crawler_name = ""
    # creation_date is supposed to be the date the news was added to our database, a datetime object
    creation_date = None