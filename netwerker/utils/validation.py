from datetime import datetime, timedelta

from dateutil.parser import parse
from flask_restx import ValidationError


def parse_timestamp(timestamp: str):
    """
    Parse a timestamp string and return a datetime object.

    Args:
        timestamp (str): A string representing a timestamp.

    Returns:
        datetime: A datetime object parsed from the timestamp string.

    Raises:
        ValidationError: If the timestamp string cannot be parsed into a datetime object.
    """
    try:
        return parse(timestamp)
    except ValueError:
        raise ValidationError("Invalid timestamp")


def validate_timestamp_range(start_time: str, end_time: str, default_range: int = 30):
    """
    Validate the timestamp range, filling in default values as needed.

    Args:
        start_time (str): A string representing the start time.
        end_time (str): A string representing the end time.
        default_range (int): The default range in days to use if start_time is None.

    Returns:
        tuple: A tuple containing two datetime objects representing the start and end of the range.

    Raises:
        ValidationError: If either the start_time or end_time strings cannot be parsed into a datetime object.
    """
    now = datetime.utcnow()

    if start_time is None:
        start_time = now - timedelta(days=default_range)
    else:
        start_time = parse_timestamp(start_time)

    if end_time is None:
        end_time = now
    else:
        end_time = parse_timestamp(end_time)

    if start_time > end_time:
        raise ValidationError("start_time must be before end_time")

    return start_time, end_time
