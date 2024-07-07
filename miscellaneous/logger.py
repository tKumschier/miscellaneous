# pylint: skip-file
# mypy: disable-error-code="import-not-found"
import logging
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple, TypeVar

from pydantic import BaseModel, Field

try:
    from settings import settings
except ImportError:
    print("Logger: Settings not imported")
    pass

propertyReturn = TypeVar("propertyReturn")


def classproperty(meth: Callable[..., propertyReturn]) -> propertyReturn:
    """Access a @classmethod like a @property."""
    # mypy doesn't understand class properties yet: https://github.com/python/mypy/issues/2563
    return classmethod(property(meth))  # type: ignore


class DEFAULT_VALUES:
    log_level: str = "INFO"
    logger_name: str = "main_logger"

    @classproperty
    def save_path(_) -> Path:
        return (
            Path(sys.argv[0]).parents[1]
            / "logs"
            / (datetime.now().strftime("%Y.%m.%d") + ".log")
        )


LOG_LEVELS: dict[str, int] = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


class Logger(BaseModel):
    logger: logging.Logger = Field(...)
    log_level_is_on: dict[str, bool] = Field(...)
    problem_occurred: bool = False
    save_path: Path = Field(...)

    class Config:
        arbitrary_types_allowed = True

    def __init__(self) -> None:
        log_level, save_path, logger_name = self._get_data_from_settings()
        logger = self._get_logger(log_level, save_path, logger_name)
        log_level_is_on: dict[str, bool] = {
            key: logger.isEnabledFor(val) for (key, val) in LOG_LEVELS.items()
        }
        super().__init__(
            logger=logger, log_level_is_on=log_level_is_on, save_path=save_path
        )

    @staticmethod
    def _get_data_from_settings() -> Tuple[str, Path, str]:
        log_level = DEFAULT_VALUES.log_level
        save_path = DEFAULT_VALUES.save_path
        logger_name = DEFAULT_VALUES.logger_name

        if "settings" in sys.modules:
            if hasattr(settings, "log_level"):
                log_level = settings.log_level
            if hasattr(settings, "save_path"):
                save_path = settings.save_path
            if hasattr(settings, "logger_name"):
                logger_name = settings.logger_name
        return log_level, save_path, logger_name

    def _get_logger(
        self, log_level: str, save_path: Path, logger_name: str = "root"
    ) -> logging.Logger:
        """Helper function to setup logging. This is necessary, because the default logging does not work in the case of Parallel processing.
        https://github.com/joblib/joblib/issues/1017#issuecomment-711723073

        Args:
            log_level (str): Set the level of the log messages.

        Returns:
            Logger (logging.Logger)
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(LOG_LEVELS[log_level])

        stream_handlers = [
            handler
            for handler in logger.handlers
            if isinstance(handler, logging.StreamHandler)
        ]
        file_handlers = [
            handler
            for handler in logger.handlers
            if isinstance(handler, logging.FileHandler)
        ]
        if len(stream_handlers) == 0:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(
                logging.Formatter("%(levelname)-8s %(message)s")
            )
            logger.addHandler(stream_handler)

        if len(file_handlers) == 0:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(save_path, mode="w")
            file_handler.setFormatter(
                logging.Formatter("%(levelname)-8s %(asctime)-3s %(message)s")
            )
            logger.addHandler(file_handler)
        return logger

    def replace_handlers(self) -> None:
        _, _, logger_name = self._get_data_from_settings()
        for hdlr in self.logger.handlers[:]:
            if hdlr.name == logger_name:
                self.logger.removeHandler(hdlr)

        log_level, save_path, logger_name = self._get_data_from_settings()
        self._get_logger(log_level, save_path, logger_name)

    def critical(self, *args: Any) -> None:
        if self.log_level_is_on["CRITICAL"]:
            self.problem_occurred = True
            self.logger.critical(*args)

    def error(self, *args: Any) -> None:
        if self.log_level_is_on["ERROR"]:
            self.problem_occurred = True
            self.logger.error(*args)

    def warning(self, *args: Any) -> None:
        if self.log_level_is_on["WARNING"]:
            self.problem_occurred = True
            self.logger.warning(*args)

    def info(self, *args: Any) -> None:
        if self.log_level_is_on["INFO"]:
            self.logger.info(*args)

    def debug(self, *args: Any) -> None:
        if self.log_level_is_on["DEBUG"]:
            self.logger.debug(*args)


logger = Logger()
