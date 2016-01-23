# -*- coding: utf-8 -*-
# Author: Álvaro Parafita (parafita.alvaro@gmail.com)


class NewsparserException(Exception):
    """ 
        Abstract Exception that sums all non-standard exceptions 
        raised by this package.
    """

    def __init__(self, feed):
        self.feed = feed


    def __str__(self):
        return 'Exception for feed "{}"'.format(self.feed.name)


class BozoException(NewsparserException):
    """
        Exception raised when a feed gets a XML parsing error.
    """

    def __init__(self, feed, j):
        self.feed = feed
        self.bozo_exception = j.get('bozo_exception', [])


class LostFeedException(NewsparserException):
    """
        Exception raised when we a 4XX status code for a given feed
    """

    def __init__(self, feed, j):
        self.feed = feed
        self.j = j