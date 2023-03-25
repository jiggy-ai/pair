

class MinimumTokenLimit(Exception):
    """
    The specified minimum token count has been exceeded
    """
    
class MaximumTokenLimit(Exception):
    """
    The specified maximum token count has been exceeded
    """



class ExtractException(Exception):
    """
    various extraction errors
    """
    
class UnsupportedHostException(ExtractException):
    """
    The URL is for a host we know we can't access reliably
    """

class UnsupportedContentType(ExtractException):
    """
    The http content type is unsupported.
    """
    
class EmptyText(ExtractException):
    """
    Unable to extract any readable text from the URL.
    """


class NetworkError(ExtractException):
    """
    Unable to access the content.
    """

    
