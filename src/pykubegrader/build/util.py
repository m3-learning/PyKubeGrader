from datetime import datetime
from dateutil import parser


def get_due_date(assignment):
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