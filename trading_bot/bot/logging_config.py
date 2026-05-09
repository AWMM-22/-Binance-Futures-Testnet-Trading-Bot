from pathlib import Path

from loguru import logger


LOG_FILE = Path("logs") / "trading_bot.log"


def init_logging(verbose: bool) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()

    level = "DEBUG" if verbose else "INFO"
    logger.add(
        LOG_FILE,
        rotation="5 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
    logger.add(
        sink=lambda message: print(message, end=""),
        level=level,
        format="{time:HH:mm:ss} | {level} | {message}",
    )
