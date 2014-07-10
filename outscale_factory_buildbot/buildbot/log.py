"""
Logging configuration
"""
import logging


def _loglevel_string_to_object(loglevel_string):
    """
    Convert loglevel string to object.
    """
    return getattr(logging, loglevel_string)


def configure_logging(c, fc, repos, meta):
    """
    Configure logging.
    """
    string_default = fc.get('loglevel_default', 'INFO')
    string_boto = fc.get('loglevel_boto', 'INFO')
    level_default = _loglevel_string_to_object(string_boto)
    level_boto = _loglevel_string_to_object(string_default)
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=level_default)
    logging.getLogger('boto').setLevel(level_boto)
