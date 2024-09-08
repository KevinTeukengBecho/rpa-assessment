"""Module for custom exceptions"""


class ScrapeException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class SearchPhraseContainsNoResultsException(ScrapeException):
    pass


class NewsCategoryNotFoundException(ScrapeException):
    pass


class ParseNewsDateException(ScrapeException):
    pass


class UnexpectedEndOfNavigation(ScrapeException):
    pass
