import os
import sys
import logging
import logging.handlers
import traceback
from config import CONFIG

DEFAULT_LOG_PATH = os.getcwd() + "/log/"

class LOG():
    cli_log_flag = False
    trace_log_flag = False

    LOG = logging.getLogger(__name__)

    @classmethod
    def set_default_log(cls, file_name):
        if not os.path.exists(DEFAULT_LOG_PATH):
            os.makedirs(DEFAULT_LOG_PATH)

        log_formatter = logging.Formatter('[%(asctime)s] %(message)s')

        # set file name
        file_name = DEFAULT_LOG_PATH + file_name

        # use cli rotate/backup config
        file_handler = logging.handlers.TimedRotatingFileHandler(file_name,
                                                                 when=CONFIG.get_cli_log_rotate(),
                                                                 backupCount=int(CONFIG.get_cli_log_backup()))

        file_handler.setFormatter(log_formatter)

        cls.LOG.addHandler(file_handler)
        cls.LOG.setLevel(logging.DEBUG)

    @classmethod
    def set_log_config(cls):
        if (CONFIG.get_cli_log().upper()) == 'ON':
            cls.cli_log_flag = True

        if (CONFIG.get_trace_log().upper()) == 'ON':
            cls.trace_log_flag = True

    @classmethod
    def exception_err_write(cls):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        cls.LOG.debug("%s", ''.join('   || ' + line for line in lines))


class USER_LOG():
    LOG = None

    def set_log(self, file_name, rotate, backup):
        self.LOG = logging.getLogger(file_name)

        if not os.path.exists(DEFAULT_LOG_PATH):
            os.makedirs(DEFAULT_LOG_PATH)

        log_formatter = logging.Formatter('[%(asctime)s] %(message)s')

        file_name = DEFAULT_LOG_PATH + file_name

        file_handler = logging.handlers.TimedRotatingFileHandler(file_name,
                                                                 when=rotate,
                                                                 backupCount=backup)

        file_handler.setFormatter(log_formatter)

        self.LOG.addHandler(file_handler)
        self.LOG.setLevel(logging.DEBUG)

    def trace_log(self, log):
        try:
            if LOG.trace_log_flag:
                self.LOG.debug('[TRACE] ' + log)
        except:
            LOG.exception_err_write()

    def cli_log(self, log):
        try:
            if LOG.cli_log_flag:
                self.LOG.debug('[CLI] ' + log)
        except:
            LOG.exception_err_write()
