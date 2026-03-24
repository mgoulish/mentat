#!/usr/bin/env python3

from   datetime import datetime, timezone



def string_to_microseconds_since_epoch(s: str) -> int:
    try:
        # First try the version that includes the "+0000" (or any other +xxxx offset)
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f %z")
    except ValueError:
        # No timezone suffix present → treat as UTC 
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)

    # .timestamp() returns seconds since epoch (float); multiply by 1_000_000 for microseconds
    return int(dt.timestamp() * 1_000_000)
