import logging

try:
    from colorama import Fore
    from colorama import Style
except ImportError:
    class EmptyStringAttributes:
        def __getattr__(self, name):
            return ''
    Fore = EmptyStringAttributes()
    Style = EmptyStringAttributes()


class LogFormatter(logging.Formatter):
    def format(self, record):
        result = super(LogFormatter, self).format(record)
        level_color = None

        if record.levelno == logging.WARNING:
            level_color = Fore.YELLOW
        elif record.levelno >= logging.ERROR:
            level_color = Fore.RED

        if level_color:
            result = level_color + Style.BRIGHT + '[{}] '.format(record.levelname) + Style.RESET_ALL + Fore.RESET + result

        return result
