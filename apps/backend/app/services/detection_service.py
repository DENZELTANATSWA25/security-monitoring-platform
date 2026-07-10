from datetime import datetime, timedelta


FAILED_LOGIN_THRESHOLD = 5
TIME_WINDOW_MINUTES = 10


def detect_bruteforce(events):
    """
    Detect possible brute force login attempts.

    Returns True if suspicious activity is detected.
    """

    if not events:
        return False

    now = datetime.utcnow()

    recent_failures = [
        event
        for event in events
        if event.get("status") == "failed"
        and now - event.get("timestamp", now)
        <= timedelta(minutes=TIME_WINDOW_MINUTES)
    ]

    return len(recent_failures) >= FAILED_LOGIN_THRESHOLD
