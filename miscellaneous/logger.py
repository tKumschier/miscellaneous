# pylint: skip-file
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

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

    def __init__(self, log_level: str = "INFO") -> None:
        save_path: Path = (
            Path(__file__).absolute().parents[2]
            / "logs"
            / (datetime.now().strftime("%Y.%m.%d_%H.00") + ".log")
        )
        logger = self._get_logger(log_level, save_path)
        log_level_is_on: dict[str, bool] = {
            key: logger.isEnabledFor(val) for (key, val) in LOG_LEVELS.items()
        }
        super().__init__(
            logger=logger, log_level_is_on=log_level_is_on, save_path=save_path
        )

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

        if len(logger.handlers) == 0:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(
                logging.Formatter("%(levelname)-8s %(message)s")
            )
            logger.addHandler(stream_handler)

            save_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(save_path, mode="w")
            file_handler.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
            logger.addHandler(file_handler)
        return logger

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
