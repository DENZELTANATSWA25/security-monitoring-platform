"""Application logging configuration"""

import logging

from app.core.config import settings

def configure_logging() -> None:
    """Configure consistent application logging."""

    log_level = (
        logging.DEBUG
        if settings.APP_ENV.lower() == "development"
        else logging.INFO
    )

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        force=True,
    )

    """
    Keep third-party infrastructure logs useful without making application output excessively noisy.
    """
    logging.getLogger("sqlalachemy.engine").setLevel(
        logging.WARNING
    )