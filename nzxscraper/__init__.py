from os import path, remove
import logging
import logging.config
import json

# If applicable, delete the existing log file to generate a fresh log file during each execution

def getLogger():
    """
    This method creates the logger for the module to record information during runtime

    Before other functions can use it, it should run once to initialise the logger first

    Returns:
        Logger: logger for the module
    """
    if path.isfile("python_logging.log"):
        remove("python_logging.log")

    with open("python_logging_configuration.json", 'r') as logging_configuration_file:
        config_dict = json.load(logging_configuration_file)

    logging.config.dictConfig(config_dict)

    # Log that the logger was configured
    logger = logging.getLogger(__name__)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logger.info('Completed configuring logger()!')
    return logger

logger = getLogger()

def printProgressBar (iteration, total, prefix, suffix, decimals = 0, length = 10, fill = '█'):
    """
    To be used within loops of fixed length, to show progress

    Args:
        iteration (Int): current iteration
        total (Int): total iterations
        prefix (Str): [Optional] prefix string
        suffix (Str): [Optional] suffix string
        decimals (Int): [Optional] positive number of decimals in percent complete
        length (Int): [Optional] character length of bar
        fill (Str): [Optional] bar fill character
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('{} |{}| {}% {}'.format(prefix, bar, percent.rjust(5), suffix))