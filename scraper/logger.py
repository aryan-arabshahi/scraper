from logging import LoggerAdapter, StreamHandler, Formatter, basicConfig, DEBUG, Logger as MainLogger, ERROR, getLogger
from datetime import datetime


class Logger(LoggerAdapter):

    def __init__(self, logger: MainLogger, extra = None):
        super(Logger, self).__init__(logger, extra or {})

    @staticmethod
    def setup():
        """Setup a custom format for the logger
        """
        handler = StreamHandler()
        formatter = Formatter("%(levelname)s:%(name)s:%(message)s")
        handler.setFormatter(formatter)
        basicConfig(level=DEBUG)

    def process(self, msg, kwargs):
        return f"[{str(datetime.now())}][{self.extra.get('prefix', '')}] - {msg}", kwargs
