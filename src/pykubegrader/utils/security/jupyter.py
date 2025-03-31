import inspect
import os

def is_called_directly_from_notebook():
    """
    Determines if the current code execution is initiated directly from a Jupyter Notebook.

    This function performs several checks to ascertain whether the code is being run
    within a Jupyter Notebook environment. It considers the type of shell being used,
    the presence of Otter Grader, and the stack trace to make this determination.

    Returns:
        bool: 
            - True if the code is executed directly from a Jupyter Notebook.
            - False if executed from other environments or if Otter Grader is detected.
    """

    # Attempt to identify the shell environment
    try:
        from IPython.core.getipython import get_ipython

        shell = get_ipython().__class__.__name__
        if shell != "ZMQInteractiveShell":
            return False
    except Exception:
        return False

    # Retrieve the current stack trace
    stack = inspect.stack()

    # Heuristic checks for Otter Grader presence
    for frame_info in stack:
        if "otter" in frame_info.filename.lower():
            return False
        if "__otter__" in frame_info.frame.f_globals:
            return False

    # Environment variable check for Otter Grader
    if os.environ.get("OTTER_GRADER_RUNNING") == "1":
        return False

    # Direct call verification
    if len(stack) < 3:
        return False

    caller_frame = stack[2].frame
    return (
        caller_frame.f_globals.get("__name__") == "__main__"
        and "__file__" not in caller_frame.f_globals
    )


def block_direct_notebook_calls(func):
    """
    Decorator to prevent direct calls to functions from Jupyter Notebooks.

    This decorator ensures that the decorated function cannot be executed directly
    from a Jupyter Notebook. It raises a RuntimeError if an attempt is made to call
    the function from within a notebook environment. This is particularly useful for
    preventing the accidental execution of grading or sensitive functions within the
    notebook.

    Args:
        func (function): The function to be decorated.

    Returns:
        function: The wrapped function that includes the check for direct notebook calls.

    Raises:
        RuntimeError: If the function is called directly from a Jupyter Notebook.
    """
    def wrapper(*args, **kwargs):
        if is_called_directly_from_notebook():
            raise RuntimeError(
                f"Direct calls to `{func.__name__}` are not allowed in a Jupyter Notebook."
            )
        return func(*args, **kwargs)

    return wrapper