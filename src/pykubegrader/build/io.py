import json
import os
from pathlib import Path
import shutil


def remove_file_suffix(dist_folder: str, suffix: str = "_temp", logger: None = None) -> None:
    """
    Removes a specified suffix from filenames within a given directory and its subdirectories.

    This function traverses the directory tree starting from the specified distribution folder,
    identifies files with the given suffix in their names, and renames them by removing the suffix.
    If a logger is provided, it logs the actions performed.

    Args:
        dist_folder (str): The root directory where the search and rename operation will be performed.
        suffix (str, optional): The suffix to be removed from filenames. Defaults to "_temp".
        logger (optional): An object with a `print_and_log` method for logging actions. Defaults to None.

    Returns:
        None
    """
    if logger is not None:
        logger.print_and_log(f"Removing postfix '{suffix}' from filenames in {dist_folder}")
    for root, _, files in os.walk(dist_folder):
        for file in files:
            if suffix in file:
                old_file_path = os.path.join(root, file)
                new_file_path = os.path.join(root, file.replace(suffix, ""))
                os.rename(old_file_path, new_file_path)

                if logger is not None:
                    logger.print_and_log(f"Renamed: {old_file_path} -> {new_file_path}")


def get_notebooks_recursively(root_folder, **kwargs):
    """
    Recursively retrieves files with a specified extension from a directory and its subdirectories.

    This function explores the directory tree starting from the given root folder, finds all files
    with the specified extension (default is .ipynb), and compiles their paths into a list.

    Args:
        root_folder (str): The root directory to initiate the search.
        **kwargs: Additional keyword arguments.
            - extension (str): The file extension to look for (default is ".ipynb").

    Returns:
        list: A list containing paths to files with the specified extension located within the root folder and its subdirectories.
    """
    extension = kwargs.get("extension", ".ipynb")

    files = []

    # Walk through the root folder and its subfolders
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            # Check if the file has the specified extension
            if filename.endswith(extension):
                notebook_path = os.path.join(dirpath, filename)
                files.append(notebook_path)
    return files


def write_JSON(**kwargs):
    """
    Writes the provided information to a JSON file.

    This method takes in keyword arguments to specify the base folder, information to be written,
    and the indentation level for the JSON file. It constructs the file path for the JSON file
    and writes the information to it.

    Args:
        **kwargs: Arbitrary keyword arguments.
            - base_folder (str): The base folder where the JSON file will be saved.
            - information (dict): The information to be written to the JSON file.
            - indent (int): The indentation level for the JSON file (default is 2).

    Returns:
        None
    """
    base_folder = kwargs.get("base_folder", None)
    information = kwargs.get("information", None)
    indent = kwargs.get("indent", 2)

    path = os.path.join(base_folder, "total_points.json")

    with open(path, "w") as json_file:
        json.dump(
            information, json_file, indent=indent
        )


def check_if_file_in_folder(folder, file):
    """
    Determines the presence of a specified file within a directory or its subdirectories.

    This function navigates through the directory structure starting from the given folder
    to locate the specified file.

    Args:
        folder (str): The directory path to begin the search.
        file (str): The filename to look for.

    Returns:
        bool: Returns True if the file is located within the folder or any of its subdirectories; 
              otherwise, returns False.
    """
    for _, _, files in os.walk(folder):
        if file in files:
            return True
    return False


def copy_files(root_folder: str, notebook_subfolder: str, files: list[str], logger: None = None) -> None:
    """
    Copies specified files from the root folder to a given notebook subfolder.

    This method iterates over a list of files and copies each file from the root folder
    to the specified notebook subfolder. It prints a message for each file being copied.

    Args:
        notebook_subfolder (str): The destination subfolder where files will be copied.
        files (list): A list of file names to be copied.

    Returns:
        None
    """
    if files:
        for file in files:
            if logger is not None:
                logger.print_and_log(f"Copying {file} to {os.path.join(notebook_subfolder, file)}")
            shutil.copy(
                os.path.join(root_folder, file),
                os.path.join(notebook_subfolder, file),
            )


def get_filename_and_root(path: str) -> tuple[Path, str]:
    """
    Extracts the root directory and filename from a given file path.

    Args:
        path (str): The file path to process.

    Returns:
        tuple[Path, str]: A tuple containing the root directory as a Path object and the filename as a string.
    """
    path_obj = Path(path).resolve()  # Resolve the path to get an absolute path
    root_path = path_obj.parent  # Get the parent directory
    filename = path_obj.name  # Get the filename
    return root_path, filename