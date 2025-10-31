import sys
from networksecurity.logging import logger

class NetworkSecurityException(Exception):
    def __init__(self, error_message, error_details: sys):
        super().__init__(error_message)
        _, _, exc_tb = error_details.exc_info()

        self.lineno = exc_tb.tb_lineno
        self.file_name = exc_tb.tb_frame.f_code.co_filename
        self.error_message = error_message

        # Log error automatically
        logger.error(self.__str__())

    def __str__(self):
        return (
            f"Error occurred in Python script: [{self.file_name}] "
            f"at line [{self.lineno}] "
            f"with message: [{self.error_message}]"
        )


if __name__ == "__main__":
    try:
        logger.info("Entering the try block")
        a = 1 / 0  # Intentional error for testing
        print("This will not be printed", a)
    except Exception as e:
        raise NetworkSecurityException(e, sys)
