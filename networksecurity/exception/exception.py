import sys
from networksecurity.logging.logger import logging

class NetworkSecurityException(Exception):
    def __init__(self, error_message: str, error_details):
        self.error_message = error_message
        # Use sys.exc_info() for current traceback (expects error_details = sys)
        _, _, exc_tb = error_details.exc_info()
        if exc_tb:
            self.lineno = exc_tb.tb_lineno
            self.file_name = exc_tb.tb_frame.f_code.co_filename
        else:
            self.lineno = "Unknown"
            self.file_name = "Unknown"
        
        # Log the error
        logging.error(str(self))
    
    def __str__(self):
        return f"Error occurred in Python script: [{self.file_name}] at line [{self.lineno}] with message: [{self.error_message}]"