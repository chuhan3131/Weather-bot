# made by alekzum :3
from typing import Iterable, MutableMapping
import structlog
import logging.handlers
import logging
import sys
import os


LOG_DIR = "logs"
LOG_FILE = "log.log"

IS_DEBUG = bool(sys.argv[1:] and "--debug" in sys.argv[1:])

LEVEL = logging.INFO

LEVEL_INFO = logging.DEBUG if IS_DEBUG else logging.INFO
LEVEL_WARNING = logging.DEBUG if IS_DEBUG else logging.WARNING

STREAM_LEVEL = LEVEL_INFO
FILE_LEVEL = LEVEL_WARNING
TEMPFILE_LEVEL = logging.DEBUG

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)


def my_callsite_processor(
    include_filename=True,
    include_funcname=True,
    inclide_lineno=True,
    fullfile_in_debug=True,
):
    def inner(logger, method_name: str, event_dict: MutableMapping):
        file_p, file_n, func_n, line_n = (
            event_dict.pop("pathname", ""),
            event_dict.pop("filename", ""),
            event_dict.pop("func_name", ""),
            event_dict.pop("lineno", ""),
        )
        array = []
        is_debug = method_name == "debug"
        if include_filename and fullfile_in_debug and is_debug:
            array.append(file_p)
        elif include_filename:
            array.append(file_n)
        if include_funcname:
            array.append(func_n)
        if inclide_lineno:
            array.append(line_n)
        args = tuple(array)
        event_dict["modline"] = ":".join(str(i) for i in args)
        return event_dict

    return inner


def filter_my_callsite_processor(blacklist: Iterable = ()):
    def inner(logger, method_name, event):
        if any(logger.name.startswith(x) for x in blacklist):
            event.pop("modline")
        return event

    return inner


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ],
        ),
        my_callsite_processor(include_funcname=False),
        filter_my_callsite_processor(["aiogram", "pyrogram", "__main__"]),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

stream_formatter = structlog.stdlib.ProcessorFormatter(
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        # structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
)

file_formatter = structlog.stdlib.ProcessorFormatter(
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        # structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(ensure_ascii=False),
    ],
)

stream_handler = logging.StreamHandler()
file_handler = logging.handlers.TimedRotatingFileHandler(
    LOG_DIR + os.sep + LOG_FILE, encoding="utf-8", when="w0"
)
tempfile_handler = logging.FileHandler(
    LOG_DIR + os.sep + "temp" + LOG_FILE, encoding="utf-8", mode="w"
)

stream_handler.setFormatter(stream_formatter)
file_handler.setFormatter(file_formatter)
tempfile_handler.setFormatter(file_formatter)

stream_handler.setLevel(STREAM_LEVEL)
file_handler.setLevel(FILE_LEVEL)
tempfile_handler.setLevel(TEMPFILE_LEVEL)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(stream_handler)
root_logger.addHandler(file_handler)
root_logger.addHandler(tempfile_handler)
root_logger = structlog.wrap_logger(root_logger)

logger = structlog.get_logger(__name__)

logger.debug("Загружен модуль логирования", custom_level=LEVEL)

MUTEDICT = {
    "utils": logging.DEBUG,
    "httpx": LEVEL_WARNING,
    "asyncio": logging.ERROR,
    "httpcore": logging.WARNING,
    "aiogram": LEVEL_INFO,
    "html": logging.DEBUG,
}

for name, level in MUTEDICT.items():
    logging.getLogger(name).setLevel(level)
