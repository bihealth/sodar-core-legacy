"""Logging helpers for management commands in SODAR Core based sites"""

import logging

from django.conf import settings


CONSOLE_HANDLER = 'console'


class ManagementCommandLogger:
    """Management command logger wrapper for SODAR Core based sites"""

    #: Python logger used by the wrapper
    logger = None

    #: Site logging level
    site_level = getattr(
        logging, getattr(settings, 'LOGGING_LEVEL', 'INFO'), 'INFO'
    )

    #: Whether console logging is enabled
    console_log = CONSOLE_HANDLER in settings.LOGGING.get('handlers', {}).keys()

    #: Disable console output if True
    disable_output = getattr(settings, 'LOGGING_DISABLE_CMD_OUTPUT', False)

    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def log(self, message, level=logging.INFO):
        """
        Print and log output from e.g. a management command, where we always
        want to output a message but may not want to always log it.

        :param message: Output message (string)
        :param level: Log level (integer or string, default=logging.INFO)
        """
        if isinstance(level, str):
            level = getattr(logging, level)
        self.logger.log(level, message)
        if self.disable_output:
            return
        printed = False
        if level >= self.site_level:
            printed = self.console_log
        if not printed:
            print(message)

    def critical(self, message):
        """Log and print CRITICAL level message"""
        self.log(message, logging.CRITICAL)

    def error(self, message):
        """Log and print ERROR level message"""
        self.log(message, logging.ERROR)

    def warning(self, message):
        """Log and print WARNING level message"""
        self.log(message, logging.WARNING)

    def info(self, message):
        """Log and print INFO level message"""
        self.log(message, logging.INFO)

    def debug(self, message):
        """Log and print DEBUG level message"""
        self.log(message, logging.DEBUG)
