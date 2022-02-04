import logging
form = logging.Formatter("%(asctime)s : %(levelname)-5.5s : %(message)s")

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """

    Creates a new logger every time it's called to allow different
    loggers for multiple files

    Parameters
    ----------
    name: str : name of the logger

    level : level of logging you want for your logger
         (Default value = logging.INFO)

    Returns: a logger
    -------

    """
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(form)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(consoleHandler)

    return logger
