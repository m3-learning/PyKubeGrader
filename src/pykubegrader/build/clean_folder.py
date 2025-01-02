import argparse
import os
import shutil
import sys


class FolderCleaner:
    def __init__(self, root_folder: str):
        """
        Initializes the FolderCleaner with the root folder to clean.

        Args:
            root_folder (str): Path to the root folder to start cleaning.
        """
        self.root_folder = root_folder

    def delete_dist_folders(self):
        """
        Recursively deletes all folders named 'dist' starting from the root folder.
        """
        for dirpath, dirnames, filenames in os.walk(self.root_folder, topdown=False):
            if "dist" in dirnames:
                dist_path = os.path.join(dirpath, "dist")
                try:
                    shutil.rmtree(dist_path)
                    print(f"Deleted: {dist_path}")
                except Exception as e:
                    print(f"Failed to delete {dist_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Recursively delete all folders named 'dist' starting from a specified root folder."
    )
    parser.add_argument(
        "root_folder", type=str, help="Path to the root folder to process"
    )

    args = parser.parse_args()
    cleaner = FolderCleaner(root_folder=args.root_folder)
    cleaner.delete_dist_folders()


if __name__ == "__main__":
    sys.exit(main())
