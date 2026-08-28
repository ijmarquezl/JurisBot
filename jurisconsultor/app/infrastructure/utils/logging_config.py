import logging

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "jurisconsultor.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 3,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    "loggers": {
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # NOTE: logger names must match the actual module __name__ values.
        "infrastructure.ai.agents.graph_agent": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "infrastructure.ai.legacy_tools": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "infrastructure.ai.tools.drafter_tools": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "infrastructure.ai.agents.drafter_nodes": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # Legacy names kept for backwards compatibility
        "graph_agent": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "tools": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}
