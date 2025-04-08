from dataclasses import dataclass
from datetime import datetime
import shutil
from dateutil import parser
import os


def get_due_date(assignment):
    """
    Extracts and parses the due date from an assignment dictionary.

    Args:
        assignment (dict): A dictionary containing assignment details, including the due date.

    Returns:
        datetime or None: A datetime object representing the due date if parsing is successful, otherwise None.
    """
    due_date_str = assignment.get("due_date")

    # Convert due_date to a datetime object if available
    due_date = None
    if due_date_str:
        try:
            due_date = parser.parse(due_date_str)  # Automatically handles timezones
        except ValueError as e:
            print(f"Error parsing due_date: {e}")
    return due_date


def json_serial(obj):
    """
    JSON serializer for objects not serializable by default.

    Args:
        obj: The object to serialize.

    Returns:
        str: The ISO format string representation of the datetime object.

    Raises:
        TypeError: If the object is not serializable.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


@dataclass
class EncryptionKeyBaseClass:
    """
    A base class for handling encryption key paths and operations related to transferring these keys.

    Attributes:
        client_private_key_path (str): The file path to the client's private key.
        server_public_key_path (str): The file path to the server's public key.
    """

    client_private_key_path: str
    server_public_key_path: str

    @property
    def client_private_key_filename(self) -> str:
        """
        Extracts the filename from the client's private key path.

        Returns:
            str: The filename of the client's private key.
        """
        return os.path.basename(self.client_private_key_path)

    @property
    def server_public_key_filename(self) -> str:
        """
        Extracts the filename from the server's public key path.

        Returns:
            str: The filename of the server's public key.
        """
        return os.path.basename(self.server_public_key_path)

    def transfer_encryption_keys(self, temp_notebook_path: str) -> tuple:
        """
        Copies the encryption keys to the directory of the specified temporary notebook path.

        Args:
            temp_notebook_path (str): The path to the temporary notebook where the keys will be transferred.

        Returns:
            tuple: A tuple containing the paths to the copied client private key and server public key.

        Raises:
            IOError: If the file copy operation fails.
        """
        client_private_key = os.path.join(
            os.path.dirname(temp_notebook_path),
            self.client_private_key_filename,
        )
        server_public_key = os.path.join(
            os.path.dirname(temp_notebook_path),
            self.server_public_key_filename,
        )

        shutil.copy(self.client_private_key_path, client_private_key)
        shutil.copy(self.server_public_key_path, server_public_key)

        return client_private_key, server_public_key