# config logger
import logging
import utils.constants as constants

# create logger for that file
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
    
debug_handler = logging.FileHandler(constants.LOGGER_DEBUG)
debug_handler.setLevel(logging.DEBUG)
    
# filter out to show only DEBUG
    
class DebugFilter(logging.Filter):
    def filter(self, record):
           return record.levelno == logging.DEBUG
        
debug_handler.addFilter(DebugFilter())
debug_formatter = logging.Formatter(
    '[%(asctime)s] DEBUG - %(name)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
debug_handler.setFormatter(debug_formatter)
    
# info and above (app) logger
    
info_handler = logging.FileHandler(constants.LOGGER_APP)
info_handler.setLevel(logging.INFO)
    
info_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt='%d/%m/%Y %H:%M:%S'
)
info_handler.setFormatter(info_formatter)
    
# add handlers
    
logger.addHandler(debug_handler)
logger.addHandler(info_handler)

# use this to get logger

def getLogger() -> logging.Logger:
    return logger