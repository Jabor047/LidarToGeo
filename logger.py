import logging
form = logging.Formatter("%(asctime)s : %(levelname)-5.5s : %(message)s")

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(form)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(consoleHandler)

    return logger
