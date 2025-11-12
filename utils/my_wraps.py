from pathlib import Path
from logging import Logger
from importlib import import_module
from structlog import wrap_logger, get_logger
import pip


def try_import(module):
    try:
        return import_module(module)
    except Exception:
        return None


def wrap_loggers():
    wrap_loggers_module("aiogram")
    wrap_loggers_module("PIL")
    wrap_loggers_module("utils", relative_to=Path())


def wrap_loggers_module(
    module_name: str, relative_to: Path = Path(pip.__file__).parent.parent
):
    logger.debug("trying to import module", module_name=module_name)
    module = try_import(module_name)
    if module is None:
        logger.warning("Didn't found module", module_name=module_name)
        return

    path = Path(module.__file__ or "").parent

    logger.debug("finding all python files in module", module_name=module_name)
    modules = tuple(
        r
        for x in sorted(path.glob("**/[!_]*.py"))
        if x.is_file()
        and (
            r := try_import(
                x.relative_to(relative_to.absolute())
                .as_posix()
                .removesuffix(".py")
                .replace("/", ".")
            )
        )
        is not None
    )

    logger.debug(
        "finding all loggers in module's python files", module_name=module_name
    )
    modules_loggers = tuple(
        (m, _loggers)
        for m in modules
        if (
            _loggers := tuple(
                n for n in dir(m) if isinstance(getattr(m, n, None), Logger)
            )
        )
    )

    logger.debug(
        "wrapping all loggers in module's python files", module_name=module_name
    )
    for module, loggers in modules_loggers:
        for logger_ in loggers:
            raw_logger = getattr(module, logger_)
            setattr(module, logger_, wrap_logger(raw_logger))


logger = get_logger()


__all__ = [
    "wrap_loggers",
]


if __name__ == "__main__":
    wrap_loggers()
