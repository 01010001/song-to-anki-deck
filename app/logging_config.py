import logging
import os
import sys


def setup_logging():
    level_name = os.getenv("LOG_LEVEL", "DEBUG" if os.getenv("DEBUG", "true").lower() == "true" else "INFO")
    level = getattr(logging, level_name.upper(), logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Flask/Werkzeug istek logları
    logging.getLogger("werkzeug").setLevel(level)

    logging.getLogger(__name__).info("Log seviyesi: %s", level_name)
