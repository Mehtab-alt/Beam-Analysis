import logging
import sys

def setup_logging(level="INFO", log_file=None):
    """
    Configures the logging for the application.

    Args:
        level (str): The minimum logging level (e.g., 'INFO', 'DEBUG').
        log_file (str, optional): Path to the log file. If provided, logs will be
                                 written to this file.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(level.upper())

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create a handler for console output
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Create a handler for file output if a path is provided
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logging.info(f"Logging configured with level {level.upper()}")
    if log_file:
        logging.info(f"Log file available at {log_file}")