import logging
from dataclasses import dataclass

@dataclass
class Logger:
    verbose: bool = False
    log: bool = True

    def __post_init__(self, **kwargs):
        """
        Initializes the Logger class with optional keyword arguments.

        Args:
            **kwargs: Additional keyword arguments to configure the logger.
                - verbose (bool): If True, enables verbose output to the console.
                - log (bool): If True, enables logging to the logger instance.
        """
        super().__post_init__(**kwargs)
        # Initialize logger at instance level
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def print_and_log(self, message, verbose=False, log=False):
        """
        Logs a message and optionally prints it to the console.

        This method is used for logging important information and optionally
        displaying it in the console based on the `verbose` and `log` attributes.

        Args:
            message (str): The message to be logged and/or printed.

        Behavior:
            - If `self.verbose` is True, the message will be printed to the console.
            - If `self.log` is True, the message will be logged using the instance's logger.

        Example:
            self.print_and_log("Processing completed successfully.")

        Raises:
            None: This method handles exceptions internally, if any arise from logging or printing.
        """

        # Print the message to the console if verbosity is enabled
        if self.verbose or verbose:
            print(message)

        # Log the message if logging is enabled
        if self.log or log:
            self.logger.info(message)