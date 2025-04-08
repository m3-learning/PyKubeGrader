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
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


@dataclass
class EncryptionKeyBaseClass:
    client_private_key_path: str
    server_public_key_path: str

    @property
    def client_private_key_filename(self):
        return os.path.basename(self.client_private_key_path)

    @property
    def server_public_key_filename(self):
        return os.path.basename(self.server_public_key_path)

    def transfer_encryption_keys(self, temp_notebook_path):
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