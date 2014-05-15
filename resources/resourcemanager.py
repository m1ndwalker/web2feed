__author__ = 'Joel Alvim'

import sys
from os import path


def get_database_path():

    resources_folder = path.dirname(__file__)
    database_path = path.join(resources_folder, "web2feed.db")

    return database_path