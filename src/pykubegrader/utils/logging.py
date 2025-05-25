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

        This method is designed to log messages that are crucial for tracking the flow of execution
        and debugging. It provides flexibility in how messages are handled, allowing them to be
        printed to the console and/or logged to a file or other logging handlers.

        Args:
            message (str): The message to be logged and/or printed. This should be a clear and concise
                           description of the event or state being logged.

        Behavior:
            - If `self.verbose` is True or the `verbose` parameter is set to True, the message will be
              printed to the console. This is useful for real-time monitoring of the program's execution.
            - If `self.log` is True or the `log` parameter is set to True, the message will be logged
              using the instance's logger. This ensures that the message is recorded in the log file
              or any other configured logging destination.

        Example:
            To log a message and print it to the console:
            self.print_and_log("Processing completed successfully.", verbose=True, log=True)

        Raises:
            None: This method is designed to handle exceptions internally, ensuring that any issues
                  arising from logging or printing do not disrupt the program's execution.
        """

        # Print the message to the console if verbosity is enabled
        if self.verbose or verbose:
            print(message)

        # Log the message if logging is enabled
        if self.log or log:
            self.logger.info(message)