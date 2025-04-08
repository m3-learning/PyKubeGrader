import os


def remove_file_suffix(dist_folder, suffix="_temp", logger = None):
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