import logging

# Logger for cell execution
logger_code = logging.getLogger("code_logger")
logger_code.setLevel(logging.INFO)

file_handler_code = logging.FileHandler(".output_code.log")
file_handler_code.setLevel(logging.INFO)
logger_code.addHandler(file_handler_code)

# Logger for question scores etc.
logger_reduced = logging.getLogger("reduced_logger")
logger_reduced.setLevel(logging.INFO)

file_handler_reduced = logging.FileHandler(".output_reduced.log")
file_handler_reduced.setLevel(logging.INFO)
logger_reduced.addHandler(file_handler_reduced)