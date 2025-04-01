def print_assignment_info(name, jhub_user, **kwargs):
    """
    Prints assignment information.

    This function prints the assignment name and JupyterHub username if verbose mode is enabled.

    Args:
        name (str): The name of the assignment.
        jhub_user (str): The JupyterHub username of the student.
        **kwargs: Additional keyword arguments. Supports 'verbose' to enable detailed printing.

    Keyword Args:
        verbose (bool): If True, prints detailed assignment information. Defaults to False.
    """

    verbose = kwargs.get("verbose", False)

    if verbose:
        print(f"Assignment: {name}")
        print(f"Username: {jhub_user}")
