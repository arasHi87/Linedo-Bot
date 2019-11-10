class WenkuLoginError(Exception):
    """
    Login wenku8 error
    """
    pass


class WenkuGetMainPageError(Exception):
    """
    Fail to get main page
    """
    pass


class EpubstSeachError(Exception):
    """
    Fail to search Epub site
    """
    pass


class NoSearchError(Exception):
    """
    No search result
    """
    pass
